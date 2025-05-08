"""
    Design concept for Transport Protocol generalization that helps to define structure for network communications

    Types: 1, 2, 3

    Type 1: Set the value of x (bool)
        Example:
            Request:  01:01:(00|01)
            Response: 01:01:(00|01) (00:fail, 01:success)

    Type 2: Set the value of y (int32) and z (str)
        Example:
            Request:  02:04:xx:xx:xx:xx:{variable}:xx:...
            Response: 02:01:(00|01) (00:fail, 01:success)

    Type 3: Get the current value of x, y, and z (in that order)
        Example:
            Request:  03
            Response:
                03:                Type ID
                01:(00|01):        Status of command (00:no errors, 01:errors)
                01:(00|01):        Current value of x (length: 1 byte)
                04:xx:xx:xx:xx:    Current value of y (length: 4 bytes)
                {variable}:xx:...  Current value of z (variable lengt)
"""

from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Iterator, Literal, Type
from types import NoneType

from ruamel import yaml
from ruamel.yaml.error import YAMLError
from bear_tools import lumberjack

logger = lumberjack.Logger()


@dataclass
class Parameter:
    description: str
    length:      int | Literal['variable']
    value_type:  Type[int] | Type[str] | Type[bool] | None
    value:       int       | str       | bool       | None = None


@dataclass
class Command:
    id:          int
    description: str
    parameters:  list[Parameter]


@dataclass
class TransportProtocol:
    schema: list[Command]

    def __get_next_length_value_object(self, tlv: Command, data: bytes) -> Iterator[Parameter | None]:
        """
        (Generator Method)
        Get the next LV (Length-Value) object

        :param tlv: The Type-Length-Value object associated with the given data
        :param data: The raw Length-Value data to parse
        :return: The LV object corresponding to the next chunk of data or None if there are any errors
        """

        def debug() -> None:
            logger.debug(f'length: {length}, value: {value_raw.hex(":")}, parameter.value_type: {parameter.value_type}')


        if len(data) < 1:
            logger.error('Error: There is no data')
            yield None
        else:
            index:  int = 1  # skip command id byte
            length_byte_count: int = 1  # TODO: Allow user to configure this in YAML file

            # Extract ordered values for each parameter in the TLV command
            for parameter in tlv.parameters:
                length: int = data[index]
                value_raw: bytes = bytes(data[index + length_byte_count: index + length_byte_count + length])
                index += length_byte_count + length

                if parameter.value_type is bool:
                    value: int = int.from_bytes(value_raw, byteorder='big')
                    if value in (0, 1):
                        p = Parameter(
                            description=parameter.description,
                            length=length,
                            value_type=parameter.value_type,
                            value=bool(value)
                        )
                        yield p
                    else:
                        logger.error(f'Error: Expected bool (0 or 1) value. Actual value: {value}')
                        debug()
                        yield None
                elif parameter.value_type is int:
                    # TODO: Add defensive code
                    yield Parameter(
                        description=parameter.description,
                        length=length,
                        value_type=parameter.value_type,
                        value=int.from_bytes(value_raw, 'big')
                    )
                elif parameter.value_type == str:
                    logger.warning('>>>>> Point 3')
                    yield Parameter(
                        description=parameter.description,
                        length=length,
                        value_type=parameter.value_type,
                        value=value_raw.decode()
                    )
                elif parameter.value_type is None:
                    logger.warning('>>>>> Point 4')
                    yield parameter
                else:
                    logger.error(f'Error: Unexpected Length-Value value type: {parameter.value_type}')

            if index != len(data):
                _info: str = bytes(data[index:]).hex(':')
                logger.error(f'Error: Data leftover after parsing all Length-Value data: {_info}')


    def parse(self, data: bytes) -> Command | None:
        """
        Parse raw bytestream data into a Type-Length-Value (TLV) object

        :param data: The raw data to parse
        :return: The data deserialized into a TLV object if possible; None otherwise
        """

        if len(data) < 1:
            logger.error('No data sent. Nothing to parse!')
            return None

        # Extract Command ID (i.e. Type)
        command_id: int = data[0]
        command: Command | None = None
        for _command in self.schema:
            if _command.id == command_id:
                command = _command
                break
        if command is None:
            logger.error(f'Error: Command not found for id: {command_id}')
            return None

        new_command = Command(command_id, command.description, parameters=[])

        # Extract Parameters (i.e. Length-Value pairs)
        for _parameter in self.__get_next_length_value_object(command, data):
            if _parameter is None:
                logger.error(f'Error: Failed to parse data into a Command: {command}')
                return None
            else:
                new_command.parameters.append(_parameter)

        return new_command


def load(path: Path) -> TransportProtocol | None:
    """
    Load a Transport Protocol from a YAML file

    :param path: The path to a YAML file containing the Transport Protocol definition
    :return: An assembled TransportProtocol object if everything went well; None otherwise
    """

    y = yaml.YAML()
    try:
        with open(path) as f:
            try:
                protocol = y.load(f)
            except YAMLError as error:
                logger.error(f'Failed to load/parse "{path}". Error: "{error}"')
                return None
    except IOError as error:
        logger.error(f'Failed to open file: "{path}". Error: "{error}"')
        return None

    schema: list[Command] = []

    for type_dict in protocol:
        command_id:      int | None      = type_dict.get('command_id')
        description:     str | None      = type_dict.get('description')
        parameters_raw:  list[dict]      = type_dict.get('parameters', [])
        parameters:      list[Parameter] = []

        if not isinstance(command_id, int):
            logger.error(f'Unexpected class for command_id: {command_id} (type: {type(command_id)})')
            return None
        if not isinstance(description, str):
            logger.error(f'Unexpected class for description: {description} (type: {type(description)})')
            return None

        # Get parameters
        for parameter in parameters_raw:
            # Get description
            parameter_description: str | None = parameter.get('description')
            if parameter_description is None:
                logger.error(f'No description defined for parameter: {parameter}')
                return None

            # Get length
            length_raw = parameter.get('length')
            if length_raw is None:
                logger.error(f'Missing length from parameter: {parameter}')
                return None
            elif not isinstance(length_raw, (int, str)):
                logger.error(f'Unexpected class for parameter.length: {length_raw} (type: {type(length_raw)}')
                return None
            elif isinstance(length_raw, str) and length_raw != 'variable':
                logger.error(f'Unexpected class for parameter.length: {length_raw} (type: {type(length_raw)}')
                return None
            else:
                length = length_raw

            # Get type
            type_raw = parameter.get('type')
            if not isinstance(type_raw, (str, NoneType)):
                logger.error(f'Unexpected class for parameter.type: {type_raw} (type: {type(type_raw)}')
                return None
            elif type_raw is None:
                value_type = None
            elif type_raw == 'int':
                value_type = int
            elif type_raw == 'str':
                value_type = str
            elif type_raw == 'bool':
                value_type = bool
            else:
                logger.error(f'Unexpected data type for parameter.type: {type_raw}. parameter: {parameter}')
                return None

            parameters.append(Parameter(parameter_description, length, value_type))

        schema.append(Command(command_id, description, parameters))

    return TransportProtocol(schema)


def main() -> None:
    path = Path('example_protocol.yaml')
    protocol = load(path)
    if protocol is None:
        logger.error(f'Failed to load/parse config file: "{path}"')
        sys.exit(1)

    def test(_data: bytes) -> None:
        _command = protocol.parse(_data)
        if isinstance(_command, Command):
            logger.warning(f'{_data.hex(":")} --> {_command}')

    test(b'\x01\x01\x00')  # ✅
    test(b'\x01\x01\x01')  # ✅
    test(b'\x01\x01\x02')  # ❌
    test(b'\x01\x00\x00')  # ❌  zero-length + value
    test(b'\x01\x02\x00')  # ❌  length mismatches value byte count


    # TODO: Should Command be broken up into CommandStructure and Command (which has values for each Parameter?


if __name__ == '__main__':
    main()
