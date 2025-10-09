import React, { useState, useEffect } from 'react';
import { Card, Button, Typography, Space, Table, Tag, Modal, Form, Input, DatePicker, message, Popconfirm, Row, Col, Statistic, Alert } from 'antd';
import {
  KeyOutlined,
  PlusOutlined,
  DeleteOutlined,
  CopyOutlined,
  ReloadOutlined
} from '@ant-design/icons';
import {
  createAPIKey,
  getAPIKeys,
  toggleAPIKey,
  deleteAPIKey,
  getUserStats
} from '../services/api';
import { useAuth } from '../components/AuthContext';
import dayjs from 'dayjs';

const { Title, Paragraph, Text } = Typography;

const APIKeyPage = () => {
  const { user } = useAuth();
  const [apiKeys, setApiKeys] = useState([]);
  const [loading, setLoading] = useState(false);
  const [userStats, setUserStats] = useState(null);
  const [newlyCreatedKey, setNewlyCreatedKey] = useState(null);

  // Modal states
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [viewKeyModalVisible, setViewKeyModalVisible] = useState(false);

  const [createForm] = Form.useForm();

  useEffect(() => {
    loadApiKeys();
    loadUserStats();
  }, []);

  const loadApiKeys = async () => {
    setLoading(true);
    try {
      const response = await getAPIKeys();
      setApiKeys(response.data);
    } catch (error) {
      message.error('加载API密钥失败');
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

  const handleCreateKey = async (values) => {
    try {
      const keyData = {
        key_name: values.key_name,
        expires_at: values.expires_at ? values.expires_at.toISOString() : null
      };

      const response = await createAPIKey(keyData);

      message.success('API密钥创建成功！');
      setCreateModalVisible(false);
      createForm.resetFields();

      // Store the newly created key to show it in a modal
      setNewlyCreatedKey(response.data);
      setViewKeyModalVisible(true);

      loadApiKeys();
      loadUserStats();
    } catch (err) {
      message.error(err.response?.data?.detail || '创建失败');
    }
  };

  const handleToggleKey = async (keyId) => {
    try {
      await toggleAPIKey(keyId);
      message.success('API密钥状态更新成功！');
      loadApiKeys();
    } catch (err) {
      message.error(err.response?.data?.detail || '更新失败');
    }
  };

  const handleDeleteKey = async (keyId) => {
    try {
      await deleteAPIKey(keyId);
      message.success('API密钥删除成功！');
      loadApiKeys();
      loadUserStats();
    } catch (err) {
      message.error(err.response?.data?.detail || '删除失败');
    }
  };

  const handleCopyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    message.success('已复制到剪贴板！');
  };

  const formatDate = (dateString) => {
    return dateString ? dayjs(dateString).format('YYYY-MM-DD HH:mm:ss') : '无限制';
  };

  const formatExpiryDate = (dateString) => {
    if (!dateString) return '永不过期';

    const expiryDate = dayjs(dateString);
    const now = dayjs();

    if (expiryDate.isBefore(now)) {
      return <Text type="danger">{expiryDate.format('YYYY-MM-DD HH:mm:ss')} (已过期)</Text>;
    } else if (expiryDate.diff(now, 'day') <= 7) {
      return <Text type="warning">{expiryDate.format('YYYY-MM-DD HH:mm:ss')} (即将过期)</Text>;
    } else {
      return expiryDate.format('YYYY-MM-DD HH:mm:ss');
    }
  };

  const columns = [
    {
      title: '密钥名称',
      dataIndex: 'key_name',
      key: 'key_name',
      render: (text) => <Text strong>{text}</Text>,
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 80,
      render: (isActive) => (
        <Tag color={isActive ? 'green' : 'red'}>
          {isActive ? '启用' : '禁用'}
        </Tag>
      ),
    },
    {
      title: '使用次数',
      dataIndex: 'usage_count',
      key: 'usage_count',
      width: 100,
      render: (count) => <Text>{count || 0}</Text>,
    },
    {
      title: '最后使用',
      dataIndex: 'last_used',
      key: 'last_used',
      width: 150,
      render: (date) => formatDate(date),
    },
    {
      title: '过期时间',
      dataIndex: 'expires_at',
      key: 'expires_at',
      width: 180,
      render: (date) => formatExpiryDate(date),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 150,
      render: (date) => formatDate(date),
    },
    {
      title: '操作',
      key: 'actions',
      width: 180,
      render: (_, record) => (
        <Space size="small">
          <Button
            type="text"
            icon={<ReloadOutlined />}
            onClick={() => handleToggleKey(record.id)}
            title={record.is_active ? '禁用' : '启用'}
          />
          <Popconfirm
            title="确定要删除这个API密钥吗？删除后无法恢复！"
            onConfirm={() => handleDeleteKey(record.id)}
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
              <KeyOutlined /> API密钥管理
            </Title>
            <Paragraph>
              生成和管理你的API密钥，用于程序化访问CodeRunner服务
            </Paragraph>

            <Alert
              message="安全提醒"
              description="API密钥等同于你的账户密码，请妥善保管！不要在代码仓库或其他公开场所暴露你的密钥。"
              type="warning"
              showIcon
              style={{ marginBottom: 24 }}
            />

            {userStats && (
              <Row gutter={16} style={{ marginBottom: 24 }}>
                <Col span={6}>
                  <Statistic
                    title="已创建密钥"
                    value={apiKeys.length}
                    suffix={`/ ${userStats.level_config?.max_api_keys === -1 ? '无限制' : userStats.level_config?.max_api_keys}`}
                    prefix={<KeyOutlined />}
                    valueStyle={{ color: '#1890ff' }}
                  />
                </Col>
                <Col span={6}>
                  <Statistic
                    title="用户等级"
                    value={userStats.level_config?.name || `等级 ${user.user_level}`}
                    prefix={<KeyOutlined />}
                    valueStyle={{ color: userStats.level_config?.color || '#666' }}
                  />
                </Col>
                <Col span={6}>
                  <Statistic
                    title="今日API调用"
                    value={userStats.today_api_calls || 0}
                    suffix={`/ ${userStats.level_config?.daily_api_calls === -1 ? '无限制' : userStats.level_config?.daily_api_calls}`}
                    prefix={<ReloadOutlined />}
                    valueStyle={{ color: '#722ed1' }}
                  />
                </Col>
                <Col span={6}>
                  <div style={{ textAlign: 'right' }}>
                    <Space>
                      <Button
                        icon={<ReloadOutlined />}
                        onClick={loadApiKeys}
                        loading={loading}
                      >
                        刷新
                      </Button>
                      <Button
                        type="primary"
                        icon={<PlusOutlined />}
                        onClick={() => setCreateModalVisible(true)}
                        disabled={userStats.level_config?.max_api_keys !== -1 && apiKeys.length >= (userStats.level_config?.max_api_keys || 5)}
                      >
                        创建密钥
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
              dataSource={apiKeys}
              columns={columns}
              rowKey="id"
              loading={loading}
              pagination={{
                pageSize: 10,
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total) => `共 ${total} 个密钥`,
              }}
              locale={{
                emptyText: '暂无API密钥，点击"创建密钥"开始创建'
              }}
            />
          </Card>
        </Col>
      </Row>

      {/* Create API Key Modal */}
      <Modal
        title="创建API密钥"
        open={createModalVisible}
        onCancel={() => {
          setCreateModalVisible(false);
          createForm.resetFields();
        }}
        footer={null}
      >
        <Form
          form={createForm}
          layout="vertical"
          onFinish={handleCreateKey}
        >
          <Form.Item
            name="key_name"
            label="密钥名称"
            rules={[{ required: true, message: '请输入密钥名称' }]}
          >
            <Input placeholder="给这个密钥起个名字，如：项目API密钥" />
          </Form.Item>

          <Form.Item
            name="expires_at"
            label="过期时间"
          >
            <DatePicker
              showTime
              placeholder="选择过期时间（可选）"
              style={{ width: '100%' }}
              disabledDate={(current) => current && current < dayjs().startOf('day')}
            />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0 }}>
            <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
              <Button onClick={() => {
                setCreateModalVisible(false);
                createForm.resetFields();
              }}>
                取消
              </Button>
              <Button type="primary" htmlType="submit">
                创建
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* View Created Key Modal */}
      <Modal
        title="API密钥创建成功"
        open={viewKeyModalVisible}
        onCancel={() => {
          setViewKeyModalVisible(false);
          setNewlyCreatedKey(null);
        }}
        footer={[
          <Button
            key="copy"
            icon={<CopyOutlined />}
            onClick={() => handleCopyToClipboard(newlyCreatedKey?.key_value)}
          >
            复制密钥
          </Button>,
          <Button
            key="ok"
            type="primary"
            onClick={() => {
              setViewKeyModalVisible(false);
              setNewlyCreatedKey(null);
            }}
          >
            我已保存
          </Button>
        ]}
      >
        {newlyCreatedKey && (
          <div>
            <Alert
              message="请立即保存这个API密钥"
              description="为了安全，这个密钥只会显示一次。请立即复制并保存在安全的地方。关闭这个对话框后将无法再次查看完整的密钥值。"
              type="error"
              showIcon
              style={{ marginBottom: 16 }}
            />

            <div style={{ marginBottom: 16 }}>
              <Text strong>密钥名称：</Text> {newlyCreatedKey.key_name}
            </div>

            <div style={{ marginBottom: 16 }}>
              <Text strong>API密钥：</Text>
              <div style={{
                background: '#f5f5f5',
                padding: '12px',
                borderRadius: '6px',
                fontFamily: 'monospace',
                fontSize: '14px',
                wordBreak: 'break-all',
                marginTop: '8px'
              }}>
                {newlyCreatedKey.key_value}
              </div>
            </div>

            <div>
              <Text strong>过期时间：</Text> {formatDate(newlyCreatedKey.expires_at)}
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default APIKeyPage;