import json
import logging
from typing import Dict, List, Any, Optional
from web3 import Web3
from web3.middleware import geth_poa_middleware
from eth_account import Account
from eth_account.signers.local import LocalAccount
import os

from app.config import settings

logger = logging.getLogger(__name__)

class EthereumClient:
    """以太坊区块链客户端"""
    
    def __init__(self, node_url: str = None, private_key: str = None):
        """
        初始化以太坊客户端
        
        Args:
            node_url: 以太坊节点URL，如果为None则使用配置中的URL
            private_key: 账户私钥，如果为None则使用配置中的私钥
        """
        self.node_url = node_url or settings.ETHEREUM_NODE_URL
        self.private_key = private_key or settings.ETHEREUM_PRIVATE_KEY
        
        # 初始化Web3连接
        self.w3 = Web3(Web3.HTTPProvider(self.node_url))
        
        # 添加POA中间件，用于连接到Goerli等测试网络
        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        
        # 检查连接
        if not self.w3.is_connected():
            logger.error(f"Failed to connect to Ethereum node at {self.node_url}")
            raise ConnectionError(f"Failed to connect to Ethereum node at {self.node_url}")
        
        # 设置账户
        if self.private_key:
            self.account: LocalAccount = Account.from_key(self.private_key)
            logger.info(f"Initialized Ethereum account: {self.account.address}")
        else:
            self.account = None
            logger.warning("No private key provided, account not initialized")
        
        logger.info(f"Connected to Ethereum node at {self.node_url}")
    
    def load_contract(self, contract_address: str, abi_path: str) -> Any:
        """
        加载智能合约
        
        Args:
            contract_address: 合约地址
            abi_path: 合约ABI文件路径
            
        Returns:
            contract: Web3合约对象
        """
        # 检查合约地址格式
        if not Web3.is_address(contract_address):
            raise ValueError(f"Invalid contract address: {contract_address}")
        
        # 加载合约ABI
        try:
            with open(abi_path, 'r') as f:
                abi = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load contract ABI from {abi_path}: {str(e)}")
            raise
        
        # 创建合约对象
        contract = self.w3.eth.contract(address=contract_address, abi=abi)
        logger.info(f"Loaded contract at {contract_address}")
        return contract
    
    def deploy_contract(self, abi_path: str, bytecode_path: str, *constructor_args) -> str:
        """
        部署智能合约
        
        Args:
            abi_path: 合约ABI文件路径
            bytecode_path: 合约字节码文件路径
            constructor_args: 合约构造函数参数
            
        Returns:
            contract_address: 部署后的合约地址
        """
        if not self.account:
            raise ValueError("Account not initialized. Private key required for deployment.")
        
        # 加载合约ABI和字节码
        try:
            with open(abi_path, 'r') as f:
                abi = json.load(f)
            
            with open(bytecode_path, 'r') as f:
                bytecode = f.read().strip()
        except Exception as e:
            logger.error(f"Failed to load contract files: {str(e)}")
            raise
        
        # 创建合约实例
        contract = self.w3.eth.contract(abi=abi, bytecode=bytecode)
        
        # 获取合约部署交易
        transaction = contract.constructor(*constructor_args).build_transaction({
            'from': self.account.address,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
            'gas': 2000000,  # 可根据需要调整
            'gasPrice': self.w3.eth.gas_price
        })
        
        # 签名交易
        signed_tx = self.account.sign_transaction(transaction)
        
        # 发送交易
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        logger.info(f"Sent contract deployment transaction: {tx_hash.hex()}")
        
        # 等待交易确认
        tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        contract_address = tx_receipt.contractAddress
        
        logger.info(f"Contract deployed at address: {contract_address}")
        return contract_address
    
    def call_contract_function(self, contract: Any, function_name: str, *args) -> Any:
        """
        调用合约函数（读取状态）
        
        Args:
            contract: Web3合约对象
            function_name: 要调用的函数名
            args: 函数参数
            
        Returns:
            result: 函数调用结果
        """
        try:
            # 获取合约函数
            contract_function = getattr(contract.functions, function_name)
            # 调用函数
            result = contract_function(*args).call()
            return result
        except Exception as e:
            logger.error(f"Failed to call contract function {function_name}: {str(e)}")
            raise
    
    def send_contract_transaction(self, contract: Any, function_name: str, *args) -> str:
        """
        发送合约交易（修改状态）
        
        Args:
            contract: Web3合约对象
            function_name: 要调用的函数名
            args: 函数参数
            
        Returns:
            tx_hash: 交易哈希
        """
        if not self.account:
            raise ValueError("Account not initialized. Private key required for transactions.")
        
        try:
            # 获取合约函数
            contract_function = getattr(contract.functions, function_name)
            
            # 构建交易
            transaction = contract_function(*args).build_transaction({
                'from': self.account.address,
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
                'gas': 2000000,  # 可根据需要调整
                'gasPrice': self.w3.eth.gas_price
            })
            
            # 签名交易
            signed_tx = self.account.sign_transaction(transaction)
            
            # 发送交易
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            logger.info(f"Sent contract transaction {function_name}: {tx_hash.hex()}")
            
            return tx_hash.hex()
        except Exception as e:
            logger.error(f"Failed to send contract transaction {function_name}: {str(e)}")
            raise
    
    def get_transaction_receipt(self, tx_hash: str) -> Dict:
        """
        获取交易收据
        
        Args:
            tx_hash: 交易哈希
            
        Returns:
            receipt: 交易收据
        """
        try:
            # 将字符串哈希转换为字节
            if isinstance(tx_hash, str) and tx_hash.startswith('0x'):
                tx_hash = bytes.fromhex(tx_hash[2:])
                
            receipt = self.w3.eth.get_transaction_receipt(tx_hash)
            return dict(receipt)
        except Exception as e:
            logger.error(f"Failed to get transaction receipt for {tx_hash}: {str(e)}")
            raise