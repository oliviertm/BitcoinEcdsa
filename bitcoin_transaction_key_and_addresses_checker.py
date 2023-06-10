from hashlib import sha256
from hashlib import new as newhash

"""
    Functions for Base 58 encoding : https://en.bitcoin.it/wiki/base58_encoding
"""
# base58 alphabet contains all letters and numbers except the ones too look alike : upper case i and lower case L, zero and upper case o
base58_alphabet = b'123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'

def b58encodeFromInt(intKey):
    """
    Base 58 encode without checksum from int
    """
    base = len(base58_alphabet)
    b58Str= b''
    while intKey:
        intKey, remainder = divmod(intKey, base)
        b58Str = base58_alphabet[remainder:remainder+1] + b58Str
    return b58Str

def b58encodeFromBytes(bytesKey):
    """
    Base 58 encode without checksum from bytes
    """
    old_len = len(bytesKey)
    strippedBytesKey = bytesKey.lstrip(b'\0')
    new_len = len(strippedBytesKey)
    acc = int.from_bytes(strippedBytesKey, byteorder='big')  # first byte is the most significant
    result = b58encodeFromInt(acc)
    return base58_alphabet[0:1] * (old_len - new_len) + result

def b58encodeFromBytesWithChecksum(bytesKey):
    """
    Base 58 encode with checksum from bytes
    """
    checksum = sha256(sha256(bytesKey).digest()).digest()
    return b58encodeFromBytes(bytesKey + checksum[:4])

def base58(hexKey):
    """
    Base 58 encode with checksum from hexadecimal string
    """
    return b58encodeFromBytesWithChecksum(bytes.fromhex(hexKey)).decode("utf-8")

def hash160(key):
    """
    Function implementing the HASH160 operation of Pkscript, using SHA256 (https://fr.m.wikipedia.org/wiki/SHA-2) and RIPEMD160 (https://fr.m.wikipedia.org/wiki/RIPEMD-160)
    """
    key_sha256=sha256(bytes.fromhex(key)).hexdigest()
    key_sha256_ripemd160 = newhash('ripemd160', bytes.fromhex(key_sha256)).hexdigest()
    return key_sha256_ripemd160

if __name__ == "__main__":
    # Address version byte : https://en.bitcoin.it/wiki/List_of_address_prefixes
    P2PKHversionByte="00" # address version used for Pubkey Hash
    P2SHversionByte="05" # address version used for Script Hash
    # Witness version : https://en.bitcoin.it/wiki/BIP_0141
    P2WPKHwitnessVersionByte = "00" # witness version used for P2WPKH
    
    """
    Code to check the keys which appears in the following transaction in the bitcoin blockchain:
     https://www.blockchain.com/btc/tx/56beef8afe5a4b5b41225211e62c3e7bce5747c4c8dcdd982173e8496687794b
    """
    print("------ transaction without witness ---------")
    
    print("__ inputs:")
    pkscript = "348ceb2e0315a310e6692c938967d8207f7dc9fd"#public key hash in  pkscript of transaction input 
    sigscript = "03416fe9ba17be8fe3f88011923135e83c6a0666fcb575de6ab337c7d6c8f41a5f"# public key in sigscript of transaction input 
    addr = "15nrxBDLts1tEbowH1dLm5z84RVas7USmP"
    print(f'sigscript pubkey :\n {sigscript} \n validates address :\n{addr} \n= {base58(P2PKHversionByte+hash160(sigscript))==addr}')
    print(f'hash160 of sigscript pubkey:\n {hash160(sigscript)} \n validates pkscript :\n {pkscript}\n = {hash160(sigscript)==pkscript}')
    print(f'pubkeyScript :\n {pkscript} \n validates address :\n{addr} \n= {base58(P2PKHversionByte+pkscript)==addr}')

    print("__ output:")
    pkscript = "07628bb59790a53711f3e9caddaa7eed89663935"#public key hash in  pkscript of transaction output 
    addr = "1g3nRQhpVo8vh6AFeGTBVkHaD9esmk8Vj"
    print(f'pubkeyScript of output :\n {pkscript} \n validates address :\n{addr} \n= {base58(P2PKHversionByte+pkscript)==addr}')
    
    """
    Code to check the keys which appears in the following transaction in the bitcoin blockchain:
     https://www.blockchain.com/btc/tx/01e7c525a5759cde1d04d2e9a363424053ace3ff1d2dde9cd1b368493254bd0d
    """
    print("------ transaction with witness ---------")
    
    print("__ inputs:")
    sigscript = "00141d41018a1c9ea2538d2c3a1ff76d9eb1640e512d" # hash is sigscript of transaction's' first input
    pkscript = "23e522dfc6656a8fda3d47b4fa53f7585ac758cd" # value to check in pkscript of transaction's' first input
    addr = "34xp4vRoCGJym3xR7yCVPFHoCNxv4Twseo" # address of transaction's first input'
    print(f'hash160 of sigscript:\n {hash160(sigscript)} \n validates pkscript :\n {pkscript}\n = {hash160(sigscript)==pkscript}')
    print(f'base58 of hash160 of sigscript:\n {base58(P2SHversionByte+hash160(sigscript))} \n validates address :\n {addr}\n = {base58(P2SHversionByte+hash160(sigscript))==addr}')
    witness = "02a720e54e39b28434a4c55462718b4584db973331a834141b8cad7e52c317f695"#public key in witness
    keyHashLen = '14' # 0x14 haxadecimal = 20 bytes key hash length (hash160 is 160 bits long = 160 bits / 8 bits = 20 bytes)
    pubKeyFromWitness = P2WPKHwitnessVersionByte + keyHashLen + hash160(witness) 
    addrFromWitness = base58( P2SHversionByte+ hash160( pubKeyFromWitness ) )
    print(f'base58 of hash160 of pubKey from witness :\n {addrFromWitness} \n validates address :\n {addr}\n = {addrFromWitness==addr}')
 