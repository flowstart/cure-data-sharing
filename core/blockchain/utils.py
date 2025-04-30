import json
import hashlib
from typing import Dict, List, Any, Optional, Union
from web3 import Web3
from eth_account import Account
from eth_account.signers.local import LocalAccount
import os

def generate_ethereum_account() -> Dict[str, str]:
    """
    生成以太坊账户
    
    Returns:
        account: 账户信息，包含地址和私钥
    """
    account: LocalAccount = Account.create()
    return {
        "address": account.address,
        "private_key": account.key.hex()
    }


def is_valid_ethereum_address(address: str) -> bool:
    """
    检查以太坊地址是否有效
    
    Args:
        address: 以太坊地址
        
    Returns:
        is_valid: 是否有效
    """
    return Web3.is_address(address)


def get_transaction_status(web3: Web3, tx_hash: str) -> Optional[Dict[str, Any]]:
    """
    获取交易状态
    
    Args:
        web3: Web3实例
        tx_hash: 交易哈希
        
    Returns:
        status: 交易状态
    """
    try:
        # 转换交易哈希格式
        if isinstance(tx_hash, str) and tx_hash.startswith('0x'):
            tx_hash_bytes = Web3.to_bytes(hexstr=tx_hash)
        else:
            tx_hash_bytes = tx_hash
            
        # 获取交易收据
        receipt = web3.eth.get_transaction_receipt(tx_hash_bytes)
        
        # 转换为字典
        receipt_dict = dict(receipt)
        
        # 检查交易状态
        if receipt_dict.get('status') == 1:
            status = 'success'
        else:
            status = 'failed'
        
        return {
            'status': status,
            'block_number': receipt_dict.get('blockNumber'),
            'gas_used': receipt_dict.get('gasUsed'),
            'transaction_hash': receipt_dict.get('transactionHash').hex()
        }
    except Exception as e:
        return None


def sign_message(private_key: str, message: str) -> str:
    """
    使用私钥签名消息
    
    Args:
        private_key: 私钥
        message: 消息
        
    Returns:
        signature: 签名
    """
    # 创建账户
    account = Account.from_key(private_key)
    
    # 对消息进行哈希
    message_hash = Web3.keccak(text=message)
    
    # 签名消息
    signed_message = account.sign_message(message_hash)
    
    return signed_message.signature.hex()


def verify_signature(message: str, signature: str, address: str) -> bool:
    """
    验证签名
    
    Args:
        message: 消息
        signature: 签名
        address: 地址
        
    Returns:
        is_valid: 签名是否有效
    """
    try:
        # 对消息进行哈希
        message_hash = Web3.keccak(text=message)
        
        # 恢复签名者地址
        recovered_address = Account.recover_message(message_hash, signature=signature)
        
        # 验证地址
        return recovered_address.lower() == address.lower()
    except Exception:
        return False


def encode_function_data(web3: Web3, abi: Union[List[Dict], str], function_name: str, *args) -> str:
    """
    编码函数调用数据
    
    Args:
        web3: Web3实例
        abi: 合约ABI
        function_name: 函数名
        args: 函数参数
        
    Returns:
        data: 函数调用数据
    """
    # 如果ABI是字符串，尝试解析为JSON
    if isinstance(abi, str):
        abi = json.loads(abi)
    
    # 创建合约对象
    contract = web3.eth.contract(abi=abi)
    
    # 获取函数
    function = getattr(contract.functions, function_name)
    
    # 编码函数调用数据
    return function(*args).build_transaction({'gas': 0, 'gasPrice': 0, 'nonce': 0})['data']


def decode_event_logs(web3: Web3, abi: Union[List[Dict], str], logs: List[Dict]) -> List[Dict]:
    """
    解码事件日志
    
    Args:
        web3: Web3实例
        abi: 合约ABI
        logs: 日志列表
        
    Returns:
        decoded_logs: 解码后的日志列表
    """
    # 如果ABI是字符串，尝试解析为JSON
    if isinstance(abi, str):
        abi = json.loads(abi)
    
    # 创建合约对象
    contract = web3.eth.contract(abi=abi)
    
    # 解码日志
    decoded_logs = []
    for log in logs:
        # 尝试解码日志
        try:
            # 转换格式
            log_dict = {
                'address': log.get('address'),
                'topics': [Web3.to_hex(topic) if isinstance(topic, bytes) else topic for topic in log.get('topics', [])],
                'data': log.get('data'),
                'blockNumber': log.get('blockNumber'),
                'transactionHash': Web3.to_hex(log.get('transactionHash')) if log.get('transactionHash') else None,
                'transactionIndex': log.get('transactionIndex'),
                'blockHash': Web3.to_hex(log.get('blockHash')) if log.get('blockHash') else None,
                'logIndex': log.get('logIndex'),
                'removed': log.get('removed', False)
            }
            
            # 解码日志
            decoded_log = contract.events.EventName().process_log(log_dict)
            decoded_logs.append({
                'event': decoded_log.event,
                'args': dict(decoded_log.args),
                'blockNumber': decoded_log.blockNumber,
                'transactionHash': decoded_log.transactionHash.hex(),
                'logIndex': decoded_log.logIndex
            })
        except Exception:
            # 如果解码失败，添加原始日志
            decoded_logs.append(log)
    
    return decoded_logs


def estimate_gas(web3: Web3, tx: Dict[str, Any]) -> int:
    """
    估计交易所需的gas
    
    Args:
        web3: Web3实例
        tx: 交易
        
    Returns:
        gas: gas量
    """
    return web3.eth.estimate_gas(tx)


def wait_for_transaction_receipt(web3: Web3, tx_hash: str, timeout: int = 120) -> Dict[str, Any]:
    """
    等待交易收据
    
    Args:
        web3: Web3实例
        tx_hash: 交易哈希
        timeout: 超时时间（秒）
        
    Returns:
        receipt: 交易收据
    """
    # 转换交易哈希格式
    if isinstance(tx_hash, str) and tx_hash.startswith('0x'):
        tx_hash_bytes = Web3.to_bytes(hexstr=tx_hash)
    else:
        tx_hash_bytes = tx_hash
    
    # 等待交易收据
    receipt = web3.eth.wait_for_transaction_receipt(tx_hash_bytes, timeout=timeout)
    
    # 转换为字典
    return dict(receipt)


def get_event_signature(event_name: str, input_types: List[str]) -> str:
    """
    获取事件签名
    
    Args:
        event_name: 事件名
        input_types: 输入类型列表
        
    Returns:
        signature: 事件签名
    """
    # 格式化事件签名
    event_signature = f"{event_name}({','.join(input_types)})"
    
    # 计算事件签名哈希
    return Web3.keccak(text=event_signature).hex()


def get_function_signature(function_name: str, input_types: List[str]) -> str:
    """
    获取函数签名
    
    Args:
        function_name: 函数名
        input_types: 输入类型列表
        
    Returns:
        signature: 函数签名
    """
    # 格式化函数签名
    function_signature = f"{function_name}({','.join(input_types)})"
    
    # 计算函数签名哈希（前4字节）
    return Web3.keccak(text=function_signature).hex()[:10]