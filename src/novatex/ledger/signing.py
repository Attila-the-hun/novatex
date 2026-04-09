"""Ed25519 signing and verification for lease events."""
import nacl.signing
import nacl.encoding
import nacl.exceptions

from .events import LeaseEvent


def generate_keypair() -> tuple[str, str]:
    """Generate an Ed25519 keypair. Returns (private_hex, public_hex)."""
    signing_key = nacl.signing.SigningKey.generate()
    private_hex = signing_key.encode(encoder=nacl.encoding.HexEncoder).decode("ascii")
    public_hex = (
        signing_key.verify_key.encode(encoder=nacl.encoding.HexEncoder).decode("ascii")
    )
    return private_hex, public_hex


def sign_event(event: LeaseEvent, private_key_hex: str) -> LeaseEvent:
    """Sign an event with Ed25519. Returns a NEW event with signature + public_key set."""
    signing_key = nacl.signing.SigningKey(
        private_key_hex.encode("ascii"), encoder=nacl.encoding.HexEncoder
    )
    public_hex = (
        signing_key.verify_key.encode(encoder=nacl.encoding.HexEncoder).decode("ascii")
    )
    signed = signing_key.sign(event.canonical_bytes())
    return event.model_copy(
        update={
            "signature": signed.signature.hex(),
            "public_key": public_hex,
        }
    )


def verify_event(event: LeaseEvent) -> bool:
    """Verify an event's Ed25519 signature. Returns False if missing or invalid."""
    if not event.signature or not event.public_key:
        return False
    try:
        verify_key = nacl.signing.VerifyKey(
            event.public_key.encode("ascii"), encoder=nacl.encoding.HexEncoder
        )
        verify_key.verify(
            event.canonical_bytes(), bytes.fromhex(event.signature)
        )
        return True
    except nacl.exceptions.BadSignatureError:
        return False
