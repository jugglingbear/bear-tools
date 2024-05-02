"""
    Design concept for Transport Protocol generalization that can be used with TCP/IP client/server systems
    
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

import abc
from dataclasses import dataclass
from enum import Enum, IntEnum
from typing import Iterator, Literal, Type, TypedDict

class ExampleTypes(IntEnum):
    TYPE_1 = 1
    TYPE_2 = 2
    TYPE_3 = 3


@dataclass
class LV:
    description: str
    length:      int | Literal['variable']
    value_type:  Type[int] | Type[str] | Type[bool] | None
    value:       int | str | bool | None = None


@dataclass
class TLV:
    type_value: Enum
    parameters: list[LV]


@dataclass
class TransportProtocol:
    type_enum: Type[Enum]
    schema:    list[TLV]


    def __get_next_length_value_object(self, tlv: TLV, data: bytes) -> Iterator[LV | None]:
        """
        (Generator Method)
        Get the next LV (Length-Value) object 

        :param tlv: The Type-Length-Value object associated with the given data
        :param data: The raw Length-Value data to parse
        :return: The LV object corresponding to the next chunk of data or None if there are any errors
        """

        def debug():
            print(f'length: {length}, value: {value_raw}, parameter.value_type: {parameter.value_type}')

        if len(data) < 1:
            print('Error: There is no data')
            yield None
        
        else:
            i: int = 1
            for parameter in tlv.parameters:
                length: int = data[i]
                value_raw: bytes = bytes(data[i+1:i+1+length])
                i += 1 + length
                if parameter.value_type == bool:
                    value: int = int.from_bytes(value_raw, byteorder='big')
                    if value in (0, 1):
                        yield LV(parameter.description, length, bool, value=bool(value))
                    else:
                        print(f'Error: Expected bool value. Actual value: {value_raw}')
                        debug()
                        yield None
                elif parameter.value_type == int:
                    # TODO
                    print(f'Parse {value_raw} into an int')
                elif parameter.value_type == str:
                    # TODO
                    print(f'Parse {value_raw} into a str')
                elif parameter.value_type is None:
                    # TODO
                    print(f'Parse {value_raw} into None')
                else:
                    print(f'Error: Unexpected Length-Value value type: {parameter.value_type}')

            if i != len(data):
                print(f'Error: Data leftover after parsing all Length-Value data: {bytes(data[i:]).hex(":")}')



    def parse(self, data: bytes) -> TLV | None:
        """
        Parse raw bytestream data into a TLV object

        :param data: The raw data to parse
        :return: The data deserialized into a TLV object if possible; None otherwise
        """

        if len(data) < 1:
            return None
    
        # Extract Type data
        type_id: int = data[0]
        tlv: TLV | None = None
        for _tlv in self.schema:
            if _tlv.type_value == type_id:
                tlv = _tlv
                break
        if tlv is None:
            print(f'Error: TLV not found for type id: {type_id}')
            return None

        print(f'tlv: {tlv}')

        # Extract Length-Value data
        length_value_data: list[LV] = []
        for _lv in self.__get_next_length_value_object(tlv, data):
            if _lv is None:
                print(f'Error: Failed to parse data into TLV: {tlv}')
                return None
            else:
                length_value_data.append(_lv)
        
        print(f'Length-Value Data:')
        for _lv in length_value_data:
            print(f'    {_lv}')


def main():
    protocol = TransportProtocol(
        ExampleTypes, [
        TLV(
            ExampleTypes.TYPE_1, 
            [
                LV('Set the value of x', 1, bool)
            ]
        ),
        TLV(
            ExampleTypes.TYPE_2, 
            [
                LV('Set the value of y', 4, int),
                LV('Set the value of z', 'variable', str)
            ]
        ),
        TLV(
            ExampleTypes.TYPE_3,
            [
                LV('Get the current value of x, y, and z', 0, None)
            ]
        )
    ])

    tlv: TLV | None = protocol.parse(bytes.fromhex('01:01:01'.replace(':', '')))



if __name__ == '__main__':
    main()

