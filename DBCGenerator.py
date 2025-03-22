import cantools.database as candb
from collections import defaultdict

class DBCGenerator:
    """
    DBCGenerator is a utility class for generating and updating DBC files using the cantools library.
    
    It allows you to create CAN signals and messages, group signals by frame IDs, and then commit these
    messages (frames) to a DBC file. The class supports specifying conversion parameters (scale and offset)
    for signals and setting message-level attributes (like VFrameFormat) to distinguish between protocols
    (e.g., Standard CAN, Extended CAN, or J1939).
    
    Attributes:
        DBC (Database): Loaded or newly created DBC database.
        signal_container (defaultdict): Maps frame IDs to a list of signals for that frame.
        frame_container (list): List of message objects (frames).
        dbcSpec (DBCSpecifics): Global DBC specifics containing attribute definitions.
        vframe_format (AttributeDefinition): Definition for VFrameFormat attribute used to tag messages.
    """
    
    def __init__(self, existing_dbc=None) -> None:
        """
        Initialize the DBCGenerator.
        
        Args:
            existing_dbc (str, optional): Path to an existing DBC file. If provided, the file is loaded.
        """
        # Load an existing DBC file if provided, otherwise start with None.
        self.DBC = candb.load_file(existing_dbc) if existing_dbc else None
        # Dictionary mapping frame_id to a list of signals.
        self.signal_container = defaultdict(list)
        # List of messages (frames) that will be added to the DBC.
        self.frame_container = []
        self.conversion = None
        
        # Define the VFrameFormat attribute for message-level information.
        self.vframe_format = candb.can.attribute_definition.AttributeDefinition(
            name="VFrameFormat",
            default_value=3,  # 0: Standard CAN, 1: Extended CAN, 3: J1939
            type_name='INT',
            kind='BO_',  # Indicates that this attribute applies to messages (frames)
            choices=['StandardCAN', 'ExtendedCAN', 'reserved', 'J1939PG']
        )
        
        # Global DBC specifics with ProtocolType and VFrameFormat definitions.
        self.dbcSpec = candb.can.formats.dbc_specifics.DbcSpecifics(
            attribute_definitions={
                "ProtocolType": candb.can.attribute_definition.AttributeDefinition(
                    name="ProtocolType",
                    default_value='J1939',
                    type_name='STRING'
                ),
                'VFrameFormat': self.vframe_format
            }
        )
    
    def createSignal(self, frame_id, name, start, length, scale=None, offset=None, byte_order='little_endian',
                     is_signed=False, raw_initial=None, raw_invalid=None, minimum=None, maximum=None,
                     unit=None, dbc_specifics=None, comment=None, receivers=None, is_multiplexer=False,
                     multiplexer_ids=None, multiplexer_signal=None, spn=None):
        """
        Create a CAN signal and add it to the container for the given frame ID.
        
        Args:
            frame_id (int): Identifier for the frame to which this signal belongs.
            name (str): Name of the signal.
            start (int): Starting bit position.
            length (int): Length in bits.
            scale (float, optional): Scaling factor for conversion.
            offset (float, optional): Offset value for conversion.
            byte_order (str, optional): 'little_endian' or 'big_endian'. Defaults to 'little_endian'.
            is_signed (bool, optional): Whether the signal is signed. Defaults to False.
            raw_initial: Initial raw value.
            raw_invalid: Value indicating an invalid signal.
            minimum: Minimum valid value.
            maximum: Maximum valid value.
            unit (str, optional): Unit of the signal.
            dbc_specifics: Additional DBC specifics.
            comment (str, optional): Comment for the signal.
            receivers: List of receiver names.
            is_multiplexer (bool, optional): Whether this signal acts as a multiplexer.
            multiplexer_ids: Multiplexer IDs.
            multiplexer_signal: Multiplexer signal flag.
            spn (int, optional): J1939 Suspect Parameter Number.
        """
        # Create a conversion object if scale and offset are provided.
        if scale is not None and offset is not None:
            self.conversion = candb.conversion.BaseConversion.factory(scale=scale, offset=offset, is_float=False)
        else:
            self.conversion = None

        # Create the signal using the cantools Signal class.
        signal = candb.can.Signal(
            name=name,
            start=start,
            length=length,
            byte_order=byte_order,
            is_signed=is_signed,
            unit=unit,
            spn=spn,
            conversion=self.conversion,
            raw_initial=raw_initial,
            raw_invalid=raw_invalid,
            minimum=minimum,
            maximum=maximum,
            dbc_specifics=dbc_specifics,
            comment=comment,
            receivers=receivers,
            is_multiplexer=is_multiplexer,
            multiplexer_ids=multiplexer_ids,
            multiplexer_signal=multiplexer_signal
        )
        self.signal_container[frame_id].append(signal)
    
    def createMessage(self, frame_id, name, length, contained_messages=None,
                      header_id=None, header_byte_order='big_endian', unused_bit_pattern=0,
                      comment=None, senders=None, send_type=None, cycle_time=None,
                      autosar_specifics=None, is_extended_frame=False, is_fd=False, bus_name=None, signal_groups=None,
                      strict=True, protocol=None, value=None):
        """
        Create a CAN message (frame) using signals previously added for the given frame ID.
        
        Args:
            frame_id (int): The CAN frame identifier.
            name (str): Message name.
            length (int): Message length in bytes.
            contained_messages: List of contained messages.
            header_id: Header identifier.
            header_byte_order (str): Byte order for header.
            unused_bit_pattern (int): Pattern for unused bits.
            comment (str): Comment for the message.
            senders (list): List of sender names.
            send_type: Send type.
            cycle_time (int): Cycle time in milliseconds.
            autosar_specifics: Autosar specifics.
            is_extended_frame (bool): True if using an extended CAN frame.
            is_fd (bool): True if using a CAN FD frame.
            bus_name (str): Bus name.
            signal_groups: Signal groups.
            strict (bool): Strict mode flag.
            protocol (str): Protocol type (e.g., "j1939").
            value (int, optional): Override value for VFrameFormat (e.g., 0, 1, or 3).
        """
        # Optionally, create a message-specific dbc_specifics override for VFrameFormat.
        msg_spec_ext = None
        if value is not None:
            msg_spec_ext = candb.can.formats.dbc_specifics.DbcSpecifics(
                attributes={'VFrameFormat': candb.can.attribute.Attribute(
                    value=value,  # 0: Standard CAN, 1: Extended CAN, 3: J1939
                    definition=self.vframe_format
                )}
            )
        # Retrieve signals for the given frame_id.
        signals = self.signal_container[frame_id]
        # Create the message using the cantools Message class.
        frame = candb.can.Message(
            name=name,
            frame_id=frame_id,
            protocol=protocol,
            is_extended_frame=is_extended_frame,
            length=length,
            signals=signals,
            cycle_time=cycle_time,
            senders=senders,
            dbc_specifics=msg_spec_ext,
            header_id=header_id,
            contained_messages=contained_messages,
            comment=comment,
            header_byte_order=header_byte_order,
            unused_bit_pattern=unused_bit_pattern,
            send_type=send_type,
            is_fd=is_fd,
            bus_name=bus_name,
            strict=strict,
            signal_groups=signal_groups
        )
        self.frame_container.append(frame)
    
    def commit(self, output_file="TEST_db.dbc"):
        """
        Commit the generated messages to a DBC file.
        
        If an existing DBC is loaded, new messages are appended; otherwise, a new DBC database is created.
        
        Args:
            output_file (str): The output DBC file name.
        """
        if self.DBC:
            # Append new messages to the existing database.
            self.DBC.messages.extend(self.frame_container)
        else:
            self.DBC = candb.can.Database(messages=self.frame_container, dbc_specifics=self.dbcSpec)
        candb.dump_file(self.DBC, output_file)


# Example usage:
if __name__ == "__main__":
    # Define parameters for the message and signals.
    frame_id = 0x16fd3b09
    protocol = "j1939"
    is_extended_frame = True
    cycle_time = 50
    senders = ["A"]
    spn = 1586
    
    # Create an instance of the DBCGenerator.
    generator = DBCGenerator()
    
    # Create two signals that will be part of the same message.
    generator.createSignal(frame_id, "signal1", start=0, length=8, scale=10, offset=2,
                           is_signed=True, unit=None, spn=spn)
    generator.createSignal(frame_id, "signal2", start=8, length=8, is_signed=True)
    
    # Create a message that contains the signals for the specified frame ID.
    generator.createMessage(frame_id, "Msg1", length=8, protocol=protocol,
                            is_extended_frame=is_extended_frame, cycle_time=cycle_time, senders=senders)
    
    # Commit the changes to the DBC file.
    generator.commit("TEST_db.dbc")
