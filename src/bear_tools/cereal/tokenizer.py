from bear_tools import lumberjack


class Tokenizer:
    """
    Tokenize messages received from CerealClient
    """

    logger = lumberjack.Logger()

    def __init__(self, sentinel: bytes):
        """
        Initializer

        :param sentinel: A special blob of data that appears at the end of every complete message
        """

        self.sentinel: bytes = sentinel
        self.buffer: bytearray = bytearray()  # Holds partially-assembled message
        self.tokens: list[bytes] = []         # Holds fully-assembles messages


    def add(self, partial_message: bytes) -> None:
        """
        Add a message fragment and automatically parse out any new tokens

        :param partial_message: A message fragment (partial message)
        """

        if len(partial_message) < 1:
            return

        self.buffer += partial_message

        index: int = self.buffer.find(self.sentinel)
        while index >= 0:
            token: bytes = self.buffer[:index]
            self.buffer = bytearray(self.buffer[index+len(self.sentinel):])  # Jump past sentinel to start of next token
            self.tokens.append(token)
            index: int = self.buffer.find(self.sentinel)
