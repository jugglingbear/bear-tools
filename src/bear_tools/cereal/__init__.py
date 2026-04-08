from pathlib import Path

SERVER_ADDRESS:   str = 'localhost'
SERVER_PORT_BASE: int = 14441

CLIENT_COMMAND_CODE_QUIT:     bytes = b'__quit'
SERVER_COMMAND_CODE_SHUTDOWN: str = '__shutdown'
SERVER_COMMAND_GET_CONFIG:    str = '__config'
SERVER_COMMAND_ANNOTATE:      str = '__annotate:'
END_OF_MESSAGE:               bytes = b'\x00\x00\x00'  # All network messages terminated with this detectable blob

package_dir: Path = Path(__file__).parent.absolute()
config_path: Path = Path(package_dir / 'config.yaml')
