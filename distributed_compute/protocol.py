"""
Network protocol definitions for communication between coordinator and workers.
"""

import json
import struct
import socket
import cloudpickle
import zlib


# Maximum size for a single message chunk (4MB)
MAX_CHUNK_SIZE = 4 * 1024 * 1024
# Compress payloads larger than this threshold (512KB)
COMPRESSION_THRESHOLD = 512 * 1024


class MessageType:
    """Message types for coordinator-worker communication."""
    REGISTER_WORKER = "register_worker"
    WORKER_REGISTERED = "worker_registered"
    AUTH_FAILED = "auth_failed"
    HEARTBEAT = "heartbeat"
    TASK_ASSIGNMENT = "task_assignment"
    TASK_RESULT = "task_result"
    TASK_ERROR = "task_error"
    WORKER_STATUS = "worker_status"
    SHUTDOWN = "shutdown"
    SUBMIT_JOB = "submit_job"
    JOB_RESULT = "job_result"
    JOB_ERROR = "job_error"
    # New message types for chunked transmission
    CHUNK_START = "chunk_start"
    CHUNK_DATA = "chunk_data"
    CHUNK_END = "chunk_end"


class Protocol:
    """Handles message serialization and deserialization."""
    
    @staticmethod
    def serialize_message(message_type: str, payload: dict, compress: bool = None) -> bytes:
        """
        Serialize a message with type and payload.
        
        Format: [4 bytes length][1 byte flags][message data]
        Flags: bit 0 = compressed
        
        Args:
            message_type: Type of message
            payload: Message payload
            compress: Force compression on/off. If None, auto-decide based on size
        """
        message = {
            "type": message_type,
            "payload": payload
        }
        
        # Use cloudpickle to serialize the entire message (supports functions)
        serialized = cloudpickle.dumps(message)
        
        # Decide on compression
        flags = 0
        if compress is None:
            compress = len(serialized) > COMPRESSION_THRESHOLD
        
        if compress:
            serialized = zlib.compress(serialized, level=6)
            flags |= 0x01  # Set compression flag
        
        # Prepend length (4 bytes) and flags (1 byte)
        length = struct.pack('!I', len(serialized))
        flags_byte = struct.pack('B', flags)
        
        return length + flags_byte + serialized
    
    @staticmethod
    def deserialize_message(data: bytes, flags: int) -> tuple:
        """
        Deserialize a message into type and payload.
        
        Args:
            data: Serialized message data
            flags: Flags byte indicating compression, etc.
        
        Returns: (message_type, payload)
        """
        # Check if compressed
        if flags & 0x01:
            data = zlib.decompress(data)
        
        message = cloudpickle.loads(data)
        return message["type"], message["payload"]
    
    @staticmethod
    def send_message(sock: socket.socket, message_type: str, payload: dict, compress: bool = None):
        """
        Send a message through a socket.
        For large messages, automatically chunks the transmission.
        
        Args:
            sock: Socket to send through
            message_type: Type of message
            payload: Message payload
            compress: Force compression on/off
        """
        data = Protocol.serialize_message(message_type, payload, compress=compress)
        
        # If message is small enough, send directly
        if len(data) <= MAX_CHUNK_SIZE:
            sock.sendall(data)
            return
        
        # For large messages, send in chunks
        total_size = len(data)
        num_chunks = (total_size + MAX_CHUNK_SIZE - 1) // MAX_CHUNK_SIZE
        
        # Send chunk metadata first
        metadata = Protocol.serialize_message(MessageType.CHUNK_START, {
            "original_type": message_type,
            "total_size": total_size,
            "num_chunks": num_chunks
        }, compress=False)
        sock.sendall(metadata)
        
        # Send data chunks
        offset = 0
        chunk_num = 0
        while offset < total_size:
            chunk_size = min(MAX_CHUNK_SIZE, total_size - offset)
            chunk_data = data[offset:offset + chunk_size]
            
            chunk_msg = Protocol.serialize_message(MessageType.CHUNK_DATA, {
                "chunk_num": chunk_num,
                "data": chunk_data
            }, compress=False)  # Already compressed if needed
            
            sock.sendall(chunk_msg)
            
            offset += chunk_size
            chunk_num += 1
        
        # Send end marker
        end_msg = Protocol.serialize_message(MessageType.CHUNK_END, {
            "original_type": message_type
        }, compress=False)
        sock.sendall(end_msg)
    
    @staticmethod
    def receive_message(sock: socket.socket, timeout: float = None) -> tuple:
        """
        Receive a message from a socket.
        Handles chunked messages automatically.
        
        Returns: (message_type, payload)
        """
        if timeout:
            sock.settimeout(timeout)
        
        # Read the message length (4 bytes)
        length_data = Protocol._recv_exact(sock, 4)
        if not length_data:
            return None, None
        
        length = struct.unpack('!I', length_data)[0]
        
        # Read the flags byte
        flags_data = Protocol._recv_exact(sock, 1)
        if not flags_data:
            return None, None
        
        flags = struct.unpack('B', flags_data)[0]
        
        # Read the message data
        message_data = Protocol._recv_exact(sock, length)
        if not message_data:
            return None, None
        
        msg_type, payload = Protocol.deserialize_message(message_data, flags)
        
        # If this is a chunked message, receive all chunks
        if msg_type == MessageType.CHUNK_START:
            return Protocol._receive_chunked_message(sock, payload)
        
        return msg_type, payload
    
    @staticmethod
    def _recv_exact(sock: socket.socket, num_bytes: int) -> bytes:
        """Receive exactly num_bytes from socket."""
        data = b''
        while len(data) < num_bytes:
            chunk = sock.recv(num_bytes - len(data))
            if not chunk:
                return None
            data += chunk
        return data
    
    @staticmethod
    def _receive_chunked_message(sock: socket.socket, chunk_start_payload: dict) -> tuple:
        """
        Receive a chunked message.
        
        Args:
            sock: Socket to receive from
            chunk_start_payload: Payload from CHUNK_START message
        
        Returns: (original_message_type, payload)
        """
        original_type = chunk_start_payload["original_type"]
        total_size = chunk_start_payload["total_size"]
        num_chunks = chunk_start_payload["num_chunks"]
        
        # Receive all chunks
        chunks = [None] * num_chunks
        
        for _ in range(num_chunks):
            # Read chunk message
            length_data = Protocol._recv_exact(sock, 4)
            if not length_data:
                raise ConnectionError("Connection lost during chunked transfer")
            
            length = struct.unpack('!I', length_data)[0]
            
            flags_data = Protocol._recv_exact(sock, 1)
            if not flags_data:
                raise ConnectionError("Connection lost during chunked transfer")
            
            flags = struct.unpack('B', flags_data)[0]
            
            message_data = Protocol._recv_exact(sock, length)
            if not message_data:
                raise ConnectionError("Connection lost during chunked transfer")
            
            msg_type, chunk_payload = Protocol.deserialize_message(message_data, flags)
            
            if msg_type != MessageType.CHUNK_DATA:
                raise ValueError(f"Expected CHUNK_DATA, got {msg_type}")
            
            chunk_num = chunk_payload["chunk_num"]
            chunks[chunk_num] = chunk_payload["data"]
        
        # Read end marker
        length_data = Protocol._recv_exact(sock, 4)
        if length_data:
            length = struct.unpack('!I', length_data)[0]
            flags_data = Protocol._recv_exact(sock, 1)
            if flags_data:
                flags = struct.unpack('B', flags_data)[0]
                message_data = Protocol._recv_exact(sock, length)
                if message_data:
                    msg_type, end_payload = Protocol.deserialize_message(message_data, flags)
                    if msg_type != MessageType.CHUNK_END:
                        raise ValueError(f"Expected CHUNK_END, got {msg_type}")
        
        # Reconstruct full message
        full_data = b''.join(chunks)
        
        # Extract flags from first 5 bytes of reconstructed data
        length = struct.unpack('!I', full_data[:4])[0]
        flags = struct.unpack('B', full_data[4:5])[0]
        
        # Deserialize the full message
        _, payload = Protocol.deserialize_message(full_data[5:5+length], flags)
        
        return original_type, payload
