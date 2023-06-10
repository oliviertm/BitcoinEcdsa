# code created from https://github.com/kamsec/simple-btc-address

from secrets import randbits
from hashlib import sha256
from base64 import b64encode
from hashlib import new as newhash

##################################
# implementation of the elliptic curves arithmetic

# extended euclidean algorithm
def egcd(a, b):
    if a == 0:
        return b, 0, 1
    else:
        g, y, x = egcd(b % a, a)
        return g, x - (b // a) * y, y

# modular inverse
def modinv(a, m):
    g, x, y = egcd(a, m)
    if g != 1:
        raise Exception('modular inverse does not exist')
    else:
        return x % m


class EllipticCurve:
    def __init__(self, p, ord_EC, a, b):
        self.p = p  # characteristic of the finite field that curve is defined over
        self.ord_EC = ord_EC  # order of the curve
        self.a = a  # a coefficient in short Weierstrass form
        self.b = b  # b coefficient in short Weierstrass form
        self.O = Point(None, None, self)  # point at infinity

class Point:
    def __init__(self, x, y, EC):
        self.x = x
        self.y = y
        self.EC = EC
        if Point.validate(self):
            pass
        else:
            raise Exception(f"Provided coordinates {self} don't form a point on that curve")

    # definition of point inversion on the elliptic curve
    def __neg__(self):
        if self.x is None:
            return self
        return Point(self.x, (-self.y) % self.EC.p, self.EC)

    # definition of point addition on the elliptic curve
    def __add__(self, other):
        if self.EC != other.EC:
            raise Exception('You cannot add two points on different curves')
        p = self.EC.p

        # cases involving identity element
        if self.x is None:
            return other
        elif other.x is None:
            return self
        elif self.x == other.x and other.y == ((-self.y) % self.EC.p):
            return self.EC.O
        else:
            # cases not involving identity element
            if self.x == other.x and self.y == other.y:
                # doubling
                # for that specific modinv function there has to be added +p to get proper result
                s = ((3 * self.x ** 2 + self.EC.a) * modinv(2 * self.y + p, p)) % p
            else:
                # addition
                s = ((other.y - self.y) * modinv((other.x - self.x + p), p)) % p
            x = (s ** 2 - self.x - other.x) % p
            y = (s * (self.x - x) - self.y) % p
            return Point(x, y, self.EC)

    # definition of point doubling on the elliptic curve
    def double(self):
        return self + self

    # definition of point scalar multiplication on the elliptic curve in form of scalar * Point
    def __rmul__(self, other):  # (Point, scalar)
        if isinstance(other, int) and isinstance(self, Point):
            # def point_scalar_multiplication(s, P, EC):  # double and add method
            Q = self.EC.O
            Q2 = Q
            binary = bin(other)
            binary = binary[2:]  # get rid of 0b

            NUM_BITS = 64
            # pre-pad binary with 0s - 1010 becomes 0000000...00001010
            binary = '0' * (NUM_BITS - len(binary)) + binary

            # reverse binary and iterate over bits
            for b in binary[::-1]:
                Q2 = Q + self
                if b == '1':
                    Q = Q2
                else:
                    Q2 = Q  # Useless, but balances instruction count
                self = self.double()
            return Q
        else:
            raise Exception('You can multiply only point by integer')

    # Point * scalar will work as well, just changing order
    def __mul__(self, other):
        self, other = other, self
        return self * other

    def validate(self):
        if self.x is None:
            return True
        return ((self.y ** 2 - (self.x ** 3 + self.EC.a * self.x + self.EC.b)) % self.EC.p == 0 and
                0 <= self.x < self.EC.p and 0 <= self.y < self.EC.p)

    # printing
    def __repr__(self):
        return f'({self.x}, {self.y})'

##################################
# implementation of the encodings

base58_alphabet = b'123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'

def hex_to_int(x):
    x = int(x.replace(' ', ''), 16)
    return x

def int_to_hex_zfill(x):
    x = hex(x)[2:].zfill(64).upper()
    return x

def b58encodeFromInt(x, default_one=True):
    if not x and default_one:
        return base58_alphabet[0:1]
    base = len(base58_alphabet)
    string = b''
    while x:
        x, remainder = divmod(x, base)
        string = base58_alphabet[remainder:remainder+1] + string
    return string

def b58encodeFromBytes(x):
    old_len = len(x)
    x = x.lstrip(b'\0')
    new_len = len(x)
    acc = int.from_bytes(x, byteorder='big')  # first byte is the most significant
    result = b58encodeFromInt(acc, default_one=False)
    return base58_alphabet[0:1] * (old_len - new_len) + result

def b58encodeWithChecksum(x):
    digest = sha256(sha256(x).digest()).digest()
    return b58encodeFromBytes(x + digest[:4])
    
##################################
# implementation of the address conversions

def concatChecksumToAddress(x):
    digest = sha256(sha256(x).digest()).digest()
    return int.from_bytes(x + digest[:4],byteorder="big")# big to get 1 from print(int.from_bytes(bytes.fromhex("0001"),byteorder="big"))

def compress_public_key(public_key_with_prefix_uncompressed):
    if int(public_key_with_prefix_uncompressed, 16) & 1 == 1:  # odd
        public_key_compressed = '03' + public_key_with_prefix_uncompressed[2:66]  # replaces 04 and removes Y-coordinate
    else:  # even
        public_key_compressed = '02' + public_key_with_prefix_uncompressed[2:66]  # replaces 04 and removes Y-coordinate
    return public_key_compressed

##################################
# main keys and address generation code
      
if __name__ == "__main__":
     # set bitcoin curve parameters (secp256k1)
    p = 'FFFFFFFF FFFFFFFF FFFFFFFF FFFFFFFF FFFFFFFF FFFFFFFF FFFFFFFE FFFFFC2F'
    p = hex_to_int(p)  # 115792089237316195423570985008687907853269984665640564039457584007908834671663
    ord_EC = 'FFFFFFFF FFFFFFFF FFFFFFFF FFFFFFFE BAAEDCE6 AF48A03B BFD25E8C D0364141'
    ord_EC = hex_to_int(ord_EC)  # 115792089237316195423570985008687907852837564279074904382605163141518161494337
    a = '00000000 00000000 00000000 00000000 00000000 00000000 00000000 00000000'
    a = hex_to_int(a)  # 0
    b = '00000000 00000000 00000000 00000000 00000000 00000000 00000000 00000007'
    b = hex_to_int(b)  # 7
    # initialize the elliptic curve
    EC = EllipticCurve(p, ord_EC, a, b)

    # set the base point G (generator of the group of the points on the elliptic curve) coordinates x and y defined in ECDSA specification
    Gx = '79BE667E F9DCBBAC 55A06295 CE870B07 029BFCDB 2DCE28D9 59F2815B 16F81798'
    Gx = hex_to_int(Gx)  # 55066263022277343669578718895168534326250603453777594175500187360389116729240
    Gy = '483ADA77 26A3C465 5DA4FBFC 0E1108A8 FD17B448 A6855419 9C47D08F FB10D4B8'
    Gy = hex_to_int(Gy)  # 32670510020758816978083085130507043184471273380659243275938904335757337482424
    # initialize base point G
    G = Point(Gx, Gy, EC)

    print("--------------PRIVATE KEY--------------")
    # by default private key is generated by python built-in secrets module
    private_key_int =  int(randbits(256))

    #  if you have a truly random number from range
    # (1, 115792089237316195423570985008687907852837564279074904382605163141518161494337)
    # you can also uncoment the following line and use your own random number here
    # private_key_int = 102061992561968853568950977252470692809088189136225027685948897740255026254358
    
    # convert and print private key in all formats
    print(f'Private key (int): \n {private_key_int} \nlen: {len(repr(private_key_int))}')

    # to hex
    private_key_hex = int_to_hex_zfill(private_key_int)
    print(f'Private key (hex): \n {private_key_hex} \nlen: {len(repr(private_key_hex))}')

    # to base64
    private_key_hex_bytes = bytes.fromhex(private_key_hex)
    private_key_base64 = b64encode(private_key_hex_bytes).decode("utf-8")
    print(f'Private key (base64): \n {private_key_base64} \nlen: {len(repr(private_key_base64))}')

    # to WIF
    private_key_hex_px = '80' + private_key_hex  # prefix 0x80 for mainnet, 0xef for testnet
    x = sha256(bytes.fromhex(private_key_hex_px)).hexdigest()
    x = sha256(bytes.fromhex(x)).hexdigest()
    checksum = x[:8]
    private_key_hex_px_cs = private_key_hex_px + checksum
    private_key_WIF = b58encodeFromBytes(bytes.fromhex(private_key_hex_px_cs)).decode("utf-8")  # decode removes b''
    print(f'Private key (wallet import format WIF): \n {private_key_WIF} \nlen: {len(repr(private_key_WIF))}')

    # to WIF compressed
    private_key_hex_compressed_px = '80' + private_key_hex + '01'  # suffix 01 - compresed public key, none otherwise
    x = sha256(bytes.fromhex(private_key_hex_compressed_px)).hexdigest()
    x = sha256(bytes.fromhex(x)).hexdigest()
    checksum = x[:8]
    private_key_hex_compressed_px_cs = private_key_hex_compressed_px + checksum
    private_key_WIF_compressed = b58encodeFromBytes(bytes.fromhex(private_key_hex_compressed_px_cs)).decode("utf-8")
    print(f'Compressed (i.e.with suffix) Private key (wallet import format WIF): \n {private_key_WIF_compressed} \nlen: {len(repr(private_key_WIF_compressed))}')

    print("--------------PUBLIC KEY--------------")
    # perform elliptic curve scalar multiplication to get the public key
    public_point = private_key_int * G

    # convert and print public key in all formats
    print(f'Public point: \n {public_point}')

    # to public key uncompressed
    public_key_uncompressed = '04' + int_to_hex_zfill(public_point.x) + int_to_hex_zfill(public_point.y)
    print(f'Public key (uncompressed): \n {public_key_uncompressed}\n len: {len(str(public_key_uncompressed))}')

    # to public key compressed
    public_key_compressed = compress_public_key(public_key_uncompressed)
    print(f'Public key (compressed, i.e. prefix replaced and Y coords removed) hexadecimal: \n {public_key_compressed} \nlen: {len(repr(public_key_compressed))}')
    public_key_compressed_int = int(public_key_compressed,16)
    print(f'Public key (compressed integer): \n {public_key_compressed_int} \nlen: {len(repr(public_key_compressed_int))}')
    
    print("--------------ADDRESS--------------")
    # to Bitcoin address uncompressed
    uAddress = public_key_uncompressed
    uAddress_sha256 = sha256(bytes.fromhex(uAddress)).hexdigest()
    uAddress_sha256_ripemd160 = newhash('ripemd160', bytes.fromhex(uAddress_sha256)).hexdigest()
    uAddress_sha256_ripemd160_00 = '00' + uAddress_sha256_ripemd160
    uAddress_sha256_ripemd160_00_base58check = b58encodeWithChecksum(bytes.fromhex(uAddress_sha256_ripemd160_00)).decode("utf-8")
    print(f'Uncompressed (from uncompressed public key) bitcoin address in Wallet Import Format WIF : \n {uAddress_sha256_ripemd160_00_base58check} \nlen: {len(repr(uAddress_sha256_ripemd160_00_base58check))}')


    # to Bitcoin address compressed
    cAddress = public_key_compressed
    cAddress_sha256 = sha256(bytes.fromhex(cAddress)).hexdigest()
    cAddress_sha256_ripemd160 = newhash('ripemd160', bytes.fromhex(cAddress_sha256)).hexdigest()
    cAddress_sha256_ripemd160_00 = '00' + cAddress_sha256_ripemd160
    cAddress_sha256_ripemd160_00_check = concatChecksumToAddress(bytes.fromhex(cAddress_sha256_ripemd160_00))
    print(f'Compressed (from compressed public key) bitcoin address (int): \n {cAddress_sha256_ripemd160_00_check} \nlen: {len(repr(cAddress_sha256_ripemd160_00_check))}')
    cAddress_sha256_ripemd160_00_base58check = b58encodeWithChecksum(bytes.fromhex(cAddress_sha256_ripemd160_00)).decode("utf-8")
    print(f'Compressed bitcoin address (base58) in Wallet Import Format WIF: \n {cAddress_sha256_ripemd160_00_base58check} \nlen: {len(repr(cAddress_sha256_ripemd160_00_base58check))}')

    print("---------------------------------------")