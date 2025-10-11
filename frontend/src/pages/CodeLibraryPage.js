import React, { useState, useEffect, useCallback } from 'react';
import { Card, Button, Input, Typography, Space, Table, Tag, Modal, Form, message, Popconfirm, Row, Col, Statistic, Tabs, Alert, Select } from 'antd';
import {
  BookOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  CopyOutlined,
  EyeOutlined,
  ApiOutlined
} from '@ant-design/icons';
import {
  getCodeLibrary,
  deleteCodeFromLibrary,
  updateCodeInLibrary,
  saveCodeToLibrary,
  getUserStats,
  getCondaEnvironments,
  getCurrentBackendUrl
} from '../services/api';
import { useAuth } from '../components/AuthContext';

const { Title, Paragraph, Text } = Typography;
const { Search } = Input;
const { TextArea } = Input;

const CodeLibraryPage = () => {
  const { user } = useAuth();
  const [codes, setCodes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [userStats, setUserStats] = useState(null);

  // Available conda environments (fetched from backend)
  const [condaEnvs, setCondaEnvs] = useState(['base']); // Default to base only
  const [loadingEnvs, setLoadingEnvs] = useState(false);

  // Modal states
  const [addModalVisible, setAddModalVisible] = useState(false);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [viewModalVisible, setViewModalVisible] = useState(false);
  const [currentCode, setCurrentCode] = useState(null);

  // API example state
  const [apiKey, setApiKey] = useState('YOUR_API_KEY');

  const [addForm] = Form.useForm();
  const [editForm] = Form.useForm();

  const loadCodes = async () => {
    setLoading(true);
    try {
      const response = await getCodeLibrary();
      setCodes(response.data);
    } catch (error) {
      message.error('加载代码库失败');
    } finally {
      setLoading(false);
    }
  };

  const loadUserStats = async () => {
    try {
      const response = await getUserStats();
      setUserStats(response.data);
    } catch (error) {
      // Silent fail for stats
    }
  };

  const loadCondaEnvironments = useCallback(async () => {
    const controller = new AbortController();

    setLoadingEnvs(true);
    try {
      const response = await getCondaEnvironments();
      if (!controller.signal.aborted) {
        setCondaEnvs(response.data);
      }
    } catch (error) {
      if (!controller.signal.aborted) {
        console.error('Failed to load conda environments:', error);
        // Fallback to base environment if loading fails
        setCondaEnvs(['base']);
      }
    } finally {
      if (!controller.signal.aborted) {
        setLoadingEnvs(false);
      }
    }

    return () => {
      controller.abort();
    };
  }, []); // Remove loadingEnvs dependency to prevent infinite loop

  useEffect(() => {
    loadCodes();
    loadUserStats();
    loadCondaEnvironments();
  }, [loadCondaEnvironments]); // Include loadCondaEnvironments in dependencies

  const handleAddCode = async (values) => {
    try {
      await saveCodeToLibrary({
        title: values.title,
        description: values.description,
        code: values.code,
        language: 'python',
        tags: values.tags,
        conda_env: values.conda_env || 'base'
      });

      message.success('代码添加成功！');
      setAddModalVisible(false);
      addForm.resetFields();
      loadCodes();
      loadUserStats();
    } catch (err) {
      message.error(err.response?.data?.detail || '添加失败');
    }
  };

  const handleEditCode = async (values) => {
    try {
      await updateCodeInLibrary(currentCode.id, {
        title: values.title,
        description: values.description,
        code: values.code,
        tags: values.tags,
        conda_env: values.conda_env
      });

      message.success('代码更新成功！');
      setEditModalVisible(false);
      editForm.resetFields();
      setCurrentCode(null);
      loadCodes();
    } catch (err) {
      message.error(err.response?.data?.detail || '更新失败');
    }
  };

  const handleDeleteCode = async (codeId) => {
    try {
      await deleteCodeFromLibrary(codeId);
      message.success('代码删除成功！');
      loadCodes();
      loadUserStats();
    } catch (err) {
      message.error(err.response?.data?.detail || '删除失败');
    }
  };

  const handleViewCode = (code) => {
    setCurrentCode(code);
    setViewModalVisible(true);
  };

  const handleEditModalOpen = (code) => {
    setCurrentCode(code);
    editForm.setFieldsValue({
      title: code.title,
      description: code.description,
      code: code.code,
      tags: code.tags,
      conda_env: code.conda_env || 'base'
    });
    setEditModalVisible(true);
  };

  const handleCopyToClipboard = (code) => {
    navigator.clipboard.writeText(code.code);
    message.success('代码已复制到剪贴板！');
  };

  const generateCurlCommand = (codeId) => {
    const baseUrl = getCurrentBackendUrl();
    return `curl -X POST "${baseUrl}/api/v1/execute?api_key=${apiKey}" \\
  -H "Content-Type: application/json" \\
  -d '{
    "code_id": ${codeId},
    "parameters": {}
  }'`;
  };

  const generateGetCodesCurl = () => {
    const baseUrl = getCurrentBackendUrl();
    return `curl "${baseUrl}/api/v1/codes?api_key=${apiKey}&limit=10"`;
  };

  const generateGetCodeCurl = (codeId) => {
    const baseUrl = getCurrentBackendUrl();
    return `curl "${baseUrl}/api/v1/codes/${codeId}?api_key=${apiKey}"`;
  };

  const handleCopyCurlToClipboard = (curlCommand) => {
    navigator.clipboard.writeText(curlCommand);
    message.success('curl命令已复制到剪贴板！');
  };

  const filteredCodes = codes.filter(code =>
    code.title.toLowerCase().includes(searchText.toLowerCase()) ||
    code.description?.toLowerCase().includes(searchText.toLowerCase()) ||
    code.tags?.toLowerCase().includes(searchText.toLowerCase())
  );

  const columns = [
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
      render: (text, record) => (
        <div>
          <Text strong style={{ color: '#1890ff', cursor: 'pointer' }} onClick={() => handleViewCode(record)}>
            {text}
          </Text>
          {record.description && (
            <div>
              <Text type="secondary" style={{ fontSize: '12px' }}>
                {record.description}
              </Text>
            </div>
          )}
        </div>
      ),
    },
    {
      title: '标签',
      dataIndex: 'tags',
      key: 'tags',
      render: (tags) => {
        if (!tags) return '-';
        return tags.split(',').map(tag => (
          <Tag key={tag.trim()} color="blue" style={{ marginBottom: '4px' }}>
            {tag.trim()}
          </Tag>
        ));
      },
    },
    {
      title: '环境',
      dataIndex: 'conda_env',
      key: 'conda_env',
      width: 100,
      render: (conda_env) => (
        <Tag color={conda_env === 'base' ? 'default' : 'processing'}>
          {conda_env}
        </Tag>
      ),
    },
    {
      title: '语言',
      dataIndex: 'language',
      key: 'language',
      width: 80,
      render: (language) => (
        <Tag color="green">{language}</Tag>
      ),
    },
    {
      title: '更新时间',
      dataIndex: 'updated_at',
      key: 'updated_at',
      width: 150,
      render: (date) => new Date(date).toLocaleString(),
    },
    {
      title: '操作',
      key: 'actions',
      width: 200,
      render: (_, record) => (
        <Space size="small">
          <Button
            type="text"
            icon={<EyeOutlined />}
            onClick={() => handleViewCode(record)}
            title="查看"
          />
          <Button
            type="text"
            icon={<CopyOutlined />}
            onClick={() => handleCopyToClipboard(record)}
            title="复制代码"
          />
          <Button
            type="text"
            icon={<EditOutlined />}
            onClick={() => handleEditModalOpen(record)}
            title="编辑"
          />
          <Popconfirm
            title="确定要删除这段代码吗？"
            onConfirm={() => handleDeleteCode(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button
              type="text"
              danger
              icon={<DeleteOutlined />}
              title="删除"
            />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto', padding: '24px' }}>
      <Row gutter={[24, 24]}>
        <Col span={24}>
          <Card>
            <Title level={2}>
              <BookOutlined /> 我的代码库
            </Title>
            <Paragraph>
              保存和管理你的Python代码片段，随时查看和复用
            </Paragraph>

            {userStats && (
              <Row gutter={16} style={{ marginBottom: 24 }}>
                <Col span={6}>
                  <Statistic
                    title="已保存代码"
                    value={codes.length}
                    suffix={`/ ${userStats.level_config?.max_saved_codes === -1 ? '无限制' : userStats.level_config?.max_saved_codes}`}
                    prefix={<BookOutlined />}
                    valueStyle={{ color: '#1890ff' }}
                  />
                </Col>
                <Col span={6}>
                  <Statistic
                    title="用户等级"
                    value={userStats.level_config?.name || `等级 ${user.user_level}`}
                    prefix={<BookOutlined />}
                    valueStyle={{ color: userStats.level_config?.color || '#666' }}
                  />
                </Col>
                <Col span={12}>
                  <div style={{ textAlign: 'right' }}>
                    <Space>
                      <Search
                        placeholder="搜索代码标题、描述或标签..."
                        allowClear
                        enterButton
                        value={searchText}
                        onChange={(e) => setSearchText(e.target.value)}
                        style={{ width: 300 }}
                      />
                      <Button
                        type="primary"
                        icon={<PlusOutlined />}
                        onClick={() => setAddModalVisible(true)}
                      >
                        添加代码
                      </Button>
                    </Space>
                  </div>
                </Col>
              </Row>
            )}
          </Card>
        </Col>

        <Col span={24}>
          <Card>
            <Table
              dataSource={filteredCodes}
              columns={columns}
              rowKey="id"
              loading={loading}
              pagination={{
                pageSize: 10,
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total) => `共 ${total} 条记录`,
              }}
              locale={{
                emptyText: searchText ? '没有找到匹配的代码' : '暂无保存的代码，点击"添加代码"开始保存'
              }}
            />
          </Card>
        </Col>
      </Row>

      {/* Add Code Modal */}
      <Modal
        title="添加新代码"
        open={addModalVisible}
        onCancel={() => {
          setAddModalVisible(false);
          addForm.resetFields();
        }}
        footer={null}
        width={800}
      >
        <Form
          form={addForm}
          layout="vertical"
          onFinish={handleAddCode}
        >
          <Form.Item
            name="title"
            label="代码标题"
            rules={[{ required: true, message: '请输入代码标题' }]}
          >
            <Input placeholder="给你的代码起个名字..." />
          </Form.Item>

          <Form.Item
            name="description"
            label="代码描述"
          >
            <TextArea
              placeholder="简单描述这段代码的功能..."
              rows={2}
            />
          </Form.Item>

          <Form.Item
            name="code"
            label="代码内容"
            rules={[{ required: true, message: '请输入代码内容' }]}
          >
            <TextArea
              placeholder="粘贴或输入你的Python代码..."
              rows={12}
              style={{ fontSize: '14px', fontFamily: 'monospace' }}
            />
          </Form.Item>

          <Form.Item
            name="tags"
            label="标签"
          >
            <Input placeholder="用逗号分隔多个标签，如：算法,排序,Python" />
          </Form.Item>

          <Form.Item
            name="conda_env"
            label="运行环境"
            rules={[{ required: true, message: '请选择运行环境' }]}
            initialValue="base"
          >
            <Select
              placeholder="选择conda环境"
              style={{ width: '100%' }}
              loading={loadingEnvs}
              options={condaEnvs.map(env => ({
                label: env === 'base' ? `${env} (默认)` : env,
                value: env
              }))}
            />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0 }}>
            <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
              <Button onClick={() => {
                setAddModalVisible(false);
                addForm.resetFields();
              }}>
                取消
              </Button>
              <Button type="primary" htmlType="submit">
                添加
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* Edit Code Modal */}
      <Modal
        title="编辑代码"
        open={editModalVisible}
        onCancel={() => {
          setEditModalVisible(false);
          editForm.resetFields();
          setCurrentCode(null);
        }}
        footer={null}
        width={800}
      >
        <Form
          form={editForm}
          layout="vertical"
          onFinish={handleEditCode}
        >
          <Form.Item
            name="title"
            label="代码标题"
            rules={[{ required: true, message: '请输入代码标题' }]}
          >
            <Input placeholder="给你的代码起个名字..." />
          </Form.Item>

          <Form.Item
            name="description"
            label="代码描述"
          >
            <TextArea
              placeholder="简单描述这段代码的功能..."
              rows={2}
            />
          </Form.Item>

          <Form.Item
            name="code"
            label="代码内容"
            rules={[{ required: true, message: '请输入代码内容' }]}
          >
            <TextArea
              placeholder="粘贴或输入你的Python代码..."
              rows={12}
              style={{ fontSize: '14px', fontFamily: 'monospace' }}
            />
          </Form.Item>

          <Form.Item
            name="conda_env"
            label="运行环境"
            rules={[{ required: true, message: '请选择运行环境' }]}
          >
            <Select
              placeholder="选择conda环境"
              style={{ width: '100%' }}
              loading={loadingEnvs}
              options={condaEnvs.map(env => ({
                label: env === 'base' ? `${env} (默认)` : env,
                value: env
              }))}
            />
          </Form.Item>

          <Form.Item
            name="tags"
            label="标签"
          >
            <Input placeholder="用逗号分隔多个标签，如：算法,排序,Python" />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0 }}>
            <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
              <Button onClick={() => {
                setEditModalVisible(false);
                editForm.resetFields();
                setCurrentCode(null);
              }}>
                取消
              </Button>
              <Button type="primary" htmlType="submit">
                更新
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* View Code Modal */}
      <Modal
        title={currentCode?.title}
        open={viewModalVisible}
        onCancel={() => {
          setViewModalVisible(false);
          setCurrentCode(null);
        }}
        footer={[
          <Button
            key="copy"
            icon={<CopyOutlined />}
            onClick={() => handleCopyToClipboard(currentCode)}
          >
            复制代码
          </Button>,
          <Button
            key="edit"
            type="primary"
            icon={<EditOutlined />}
            onClick={() => {
              setViewModalVisible(false);
              handleEditModalOpen(currentCode);
            }}
          >
            编辑
          </Button>
        ]}
        width={900}
      >
        {currentCode && (
          <Tabs
            defaultActiveKey="code"
            items={[
              {
                key: 'code',
                label: (
                  <span>
                    <BookOutlined />
                    代码详情
                  </span>
                ),
                children: (
                  <div>
                    {currentCode.description && (
                      <div style={{ marginBottom: 16 }}>
                        <Text strong>描述：</Text>
                        <Paragraph>{currentCode.description}</Paragraph>
                      </div>
                    )}

                    {currentCode.tags && (
                      <div style={{ marginBottom: 16 }}>
                        <Text strong>标签：</Text>
                        <div style={{ marginTop: 8 }}>
                          {currentCode.tags.split(',').map(tag => (
                            <Tag key={tag.trim()} color="blue" style={{ marginBottom: '4px' }}>
                              {tag.trim()}
                            </Tag>
                          ))}
                        </div>
                      </div>
                    )}

                    <div style={{ marginBottom: 16 }}>
                      <Text strong>语言：</Text> <Tag color="green">{currentCode.language}</Tag>
                    </div>

                    <div style={{ marginBottom: 16 }}>
                      <Text strong>运行环境：</Text> <Tag color={currentCode.conda_env === 'base' ? 'default' : 'processing'}>{currentCode.conda_env}</Tag>
                    </div>

                    <div>
                      <Text strong>代码：</Text>
                      <pre style={{
                        background: '#f5f5f5',
                        padding: '16px',
                        borderRadius: '6px',
                        overflow: 'auto',
                        maxHeight: '400px',
                        fontSize: '13px',
                        fontFamily: 'monospace',
                        marginTop: '8px'
                      }}>
                        {currentCode.code}
                      </pre>
                    </div>

                    <div style={{ marginTop: 16, fontSize: '12px', color: '#666' }}>
                      创建时间：{new Date(currentCode.created_at).toLocaleString()} |
                      更新时间：{new Date(currentCode.updated_at).toLocaleString()}
                    </div>
                  </div>
                ),
              },
              {
                key: 'api',
                label: (
                  <span>
                    <ApiOutlined />
                    API调用
                  </span>
                ),
                children: (
                  <div>
                    <Alert
                      message="API调用说明"
                      description="通过API接口可以程序化地调用这段代码。请先在API密钥页面创建密钥，然后在下方设置你的API密钥。"
                      type="info"
                      showIcon
                      style={{ marginBottom: 24 }}
                    />

                    <div style={{ marginBottom: 24 }}>
                      <Text strong>API密钥设置：</Text>
                      <div style={{ marginTop: 8 }}>
                        <Input
                          placeholder="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                          value={apiKey}
                          onChange={(e) => setApiKey(e.target.value)}
                          style={{ width: '100%', maxWidth: '400px' }}
                        />
                      </div>
                    </div>

                    <div style={{ marginBottom: 24 }}>
                      <Text strong>代码ID：</Text>
                      <Text code>{currentCode.id}</Text>
                    </div>

                    <div style={{ marginBottom: 16 }}>
                      <Text strong>1. 执行代码</Text>
                      <div style={{ marginTop: 8, position: 'relative' }}>
                        <pre style={{
                          background: '#2f3349',
                          color: '#f8f8f2',
                          padding: '16px',
                          borderRadius: '6px',
                          fontSize: '12px',
                          fontFamily: 'monospace',
                          overflow: 'auto'
                        }}>
                          {generateCurlCommand(currentCode.id)}
                        </pre>
                        <Button
                          size="small"
                          icon={<CopyOutlined />}
                          onClick={() => handleCopyCurlToClipboard(generateCurlCommand(currentCode.id))}
                          style={{ position: 'absolute', top: '8px', right: '8px' }}
                        >
                          复制
                        </Button>
                      </div>
                    </div>

                    <div style={{ marginBottom: 16 }}>
                      <Text strong>2. 获取代码详情</Text>
                      <div style={{ marginTop: 8, position: 'relative' }}>
                        <pre style={{
                          background: '#2f3349',
                          color: '#f8f8f2',
                          padding: '16px',
                          borderRadius: '6px',
                          fontSize: '12px',
                          fontFamily: 'monospace',
                          overflow: 'auto'
                        }}>
                          {generateGetCodeCurl(currentCode.id)}
                        </pre>
                        <Button
                          size="small"
                          icon={<CopyOutlined />}
                          onClick={() => handleCopyCurlToClipboard(generateGetCodeCurl(currentCode.id))}
                          style={{ position: 'absolute', top: '8px', right: '8px' }}
                        >
                          复制
                        </Button>
                      </div>
                    </div>

                    <div style={{ marginBottom: 16 }}>
                      <Text strong>3. 获取所有代码列表</Text>
                      <div style={{ marginTop: 8, position: 'relative' }}>
                        <pre style={{
                          background: '#2f3349',
                          color: '#f8f8f2',
                          padding: '16px',
                          borderRadius: '6px',
                          fontSize: '12px',
                          fontFamily: 'monospace',
                          overflow: 'auto'
                        }}>
                          {generateGetCodesCurl()}
                        </pre>
                        <Button
                          size="small"
                          icon={<CopyOutlined />}
                          onClick={() => handleCopyCurlToClipboard(generateGetCodesCurl())}
                          style={{ position: 'absolute', top: '8px', right: '8px' }}
                        >
                          复制
                        </Button>
                      </div>
                    </div>

                    <Alert
                      message="注意事项"
                      description={
                        <ul style={{ margin: 0, paddingLeft: '20px' }}>
                          <li>每次API调用都会消耗你的每日调用额度</li>
                          <li>请将API密钥替换为你自己的密钥</li>
                          <li>curl命令中的参数可以根据需要调整</li>
                          <li>API基础URL：{getCurrentBackendUrl()}/api/v1</li>
                        </ul>
                      }
                      type="warning"
                      showIcon
                    />
                  </div>
                ),
              },
            ]}
          />
        )}
      </Modal>
    </div>
  );
};

export default CodeLibraryPage;