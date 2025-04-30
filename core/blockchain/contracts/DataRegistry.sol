// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title DataRegistry
 * @dev 用于注册和管理数据资产的智能合约
 */
contract DataRegistry {
    // 数据资产结构
    struct DataAsset {
        string ipfsCid;        // IPFS内容标识符
        address owner;         // 数据拥有者
        string accessPolicy;   // 访问策略(JSON字符串)
        uint256 timestamp;     // 注册时间戳
        bool isActive;         // 是否活跃
        string metadata;       // 元数据(JSON字符串)
    }
    
    // 数据访问记录结构
    struct AccessRecord {
        address user;          // 访问用户
        uint256 timestamp;     // 访问时间戳
        string purpose;        // 访问目的
    }
    
    // 数据资产映射: dataId => DataAsset
    mapping(bytes32 => DataAsset) public dataAssets;
    
    // 数据访问记录映射: dataId => AccessRecord[]
    mapping(bytes32 => AccessRecord[]) public accessRecords;
    
    // 用户拥有的数据资产: address => dataId[]
    mapping(address => bytes32[]) public userDataAssets;
    
    // 事件
    event DataAssetRegistered(bytes32 indexed dataId, address indexed owner, string ipfsCid, uint256 timestamp);
    event DataAssetUpdated(bytes32 indexed dataId, address indexed owner, string ipfsCid, uint256 timestamp);
    event DataAssetRevoked(bytes32 indexed dataId, address indexed owner, uint256 timestamp);
    event DataAssetAccessed(bytes32 indexed dataId, address indexed user, uint256 timestamp, string purpose);
    
    /**
     * @dev 注册新的数据资产
     * @param ipfsCid IPFS内容标识符
     * @param accessPolicy 访问策略(JSON字符串)
     * @param metadata 元数据(JSON字符串)
     * @return dataId 生成的数据ID
     */
    function registerDataAsset(
        string memory ipfsCid,
        string memory accessPolicy,
        string memory metadata
    ) public returns (bytes32) {
        // 生成唯一数据ID (owner地址 + ipfsCid + 时间戳的哈希值)
        bytes32 dataId = keccak256(abi.encodePacked(msg.sender, ipfsCid, block.timestamp));
        
        // 确保数据ID不存在
        require(dataAssets[dataId].owner == address(0), "Data asset already exists");
        
        // 创建数据资产
        DataAsset memory newAsset = DataAsset({
            ipfsCid: ipfsCid,
            owner: msg.sender,
            accessPolicy: accessPolicy,
            timestamp: block.timestamp,
            isActive: true,
            metadata: metadata
        });
        
        // 存储数据资产
        dataAssets[dataId] = newAsset;
        
        // 添加到用户的数据资产列表
        userDataAssets[msg.sender].push(dataId);
        
        // 触发事件
        emit DataAssetRegistered(dataId, msg.sender, ipfsCid, block.timestamp);
        
        return dataId;
    }
    
    /**
     * @dev 更新数据资产信息
     * @param dataId 数据ID
     * @param ipfsCid 新的IPFS内容标识符
     * @param accessPolicy 新的访问策略
     * @param metadata 新的元数据
     */
    function updateDataAsset(
        bytes32 dataId,
        string memory ipfsCid,
        string memory accessPolicy,
        string memory metadata
    ) public {
        // 验证数据资产存在且调用者是拥有者
        require(dataAssets[dataId].owner == msg.sender, "Not the owner or asset does not exist");
        require(dataAssets[dataId].isActive, "Data asset is not active");
        
        // 更新数据资产
        dataAssets[dataId].ipfsCid = ipfsCid;
        dataAssets[dataId].accessPolicy = accessPolicy;
        dataAssets[dataId].metadata = metadata;
        dataAssets[dataId].timestamp = block.timestamp;
        
        // 触发事件
        emit DataAssetUpdated(dataId, msg.sender, ipfsCid, block.timestamp);
    }
    
    /**
     * @dev 撤销数据资产
     * @param dataId 数据ID
     */
    function revokeDataAsset(bytes32 dataId) public {
        // 验证数据资产存在且调用者是拥有者
        require(dataAssets[dataId].owner == msg.sender, "Not the owner or asset does not exist");
        require(dataAssets[dataId].isActive, "Data asset already inactive");
        
        // 标记为非活跃
        dataAssets[dataId].isActive = false;
        
        // 触发事件
        emit DataAssetRevoked(dataId, msg.sender, block.timestamp);
    }
    
    /**
     * @dev 记录数据访问
     * @param dataId 数据ID
     * @param user 访问用户地址
     * @param purpose 访问目的
     */
    function recordAccess(
        bytes32 dataId,
        address user,
        string memory purpose
    ) public {
        // 验证数据资产存在且处于活跃状态
        require(dataAssets[dataId].isActive, "Data asset does not exist or is inactive");
        
        // 只有数据拥有者可以记录访问
        require(dataAssets[dataId].owner == msg.sender, "Only owner can record access");
        
        // 创建访问记录
        AccessRecord memory record = AccessRecord({
            user: user,
            timestamp: block.timestamp,
            purpose: purpose
        });
        
        // 添加到访问记录
        accessRecords[dataId].push(record);
        
        // 触发事件
        emit DataAssetAccessed(dataId, user, block.timestamp, purpose);
    }
    
    /**
     * @dev 获取数据资产信息
     * @param dataId 数据ID
     * @return ipfsCid IPFS内容标识符
     * @return owner 拥有者地址
     * @return accessPolicy 访问策略
     * @return timestamp 时间戳
     * @return isActive 是否活跃
     * @return metadata 元数据
     */
    function getDataAsset(bytes32 dataId) public view returns (
        string memory ipfsCid,
        address owner,
        string memory accessPolicy,
        uint256 timestamp,
        bool isActive,
        string memory metadata
    ) {
        // 获取数据资产
        DataAsset memory asset = dataAssets[dataId];
        
        // 确保数据资产存在
        require(asset.owner != address(0), "Data asset does not exist");
        
        return (
            asset.ipfsCid,
            asset.owner,
            asset.accessPolicy,
            asset.timestamp,
            asset.isActive,
            asset.metadata
        );
    }
    
    /**
     * @dev 获取用户拥有的数据资产数量
     * @param user 用户地址
     * @return count 数据资产数量
     */
    function getUserDataAssetCount(address user) public view returns (uint256) {
        return userDataAssets[user].length;
    }
    
    /**
     * @dev 获取用户拥有的数据资产ID
     * @param user 用户地址
     * @param index 索引
     * @return dataId 数据ID
     */
    function getUserDataAssetAt(address user, uint256 index) public view returns (bytes32) {
        require(index < userDataAssets[user].length, "Index out of range");
        return userDataAssets[user][index];
    }
    
    /**
     * @dev 获取访问记录数量
     * @param dataId 数据ID
     * @return count 访问记录数量
     */
    function getAccessRecordCount(bytes32 dataId) public view returns (uint256) {
        return accessRecords[dataId].length;
    }
    
    /**
     * @dev 获取访问记录
     * @param dataId 数据ID
     * @param index 索引
     * @return user 访问用户地址
     * @return timestamp 访问时间戳
     * @return purpose 访问目的
     */
    function getAccessRecordAt(bytes32 dataId, uint256 index) public view returns (
        address user,
        uint256 timestamp,
        string memory purpose
    ) {
        require(index < accessRecords[dataId].length, "Index out of range");
        
        AccessRecord memory record = accessRecords[dataId][index];
        return (
            record.user,
            record.timestamp,
            record.purpose
        );
    }
}