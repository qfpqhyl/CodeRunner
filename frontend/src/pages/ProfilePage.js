import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Card,
  Row,
  Col,
  Avatar,
  Button,
  Input,
  message,
  Spin,
  Empty,
  Space,
  Typography,
  Tag,
  Tabs,
  List,
  Statistic,
  Upload,
  Modal,
  Form,
  Select,
  Divider
} from 'antd';
import {
  UserOutlined,
  EditOutlined,
  SaveOutlined,
  UploadOutlined,
  BookOutlined,
  MessageOutlined,
  HeartOutlined,
  StarOutlined,
  EyeOutlined,
  TeamOutlined,
  CodeOutlined,
  DownloadOutlined,
  UserAddOutlined,
  UserDeleteOutlined
} from '@ant-design/icons';
import { getUserProfile, updateUserProfile, uploadAvatar, deleteAvatar, getAvatarUrl, getUserEnhancedStats, getUserActivityLogs, saveCodeToLibraryFromShare, getAvailableEnvironments, followUser, getFollowStatus, getUserByUsername, getUserPublicStats } from '../services/api';
import { useAuth } from '../components/AuthContext';
import moment from 'moment';

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;
const { TabPane } = Tabs;
const { Option } = Select;

const ProfilePage = () => {
  const navigate = useNavigate();
  const { username } = useParams();
  const { user } = useAuth();
  const [profileData, setProfileData] = useState(null);
  const [statsData, setStatsData] = useState(null);
  const [activityLogs, setActivityLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [editForm] = Form.useForm();
  const [saveCodeModal, setSaveCodeModal] = useState(false);
  const [selectedCode, setSelectedCode] = useState(null);
  const [availableEnvs, setAvailableEnvs] = useState([]);
  const [saveCodeForm] = Form.useForm();
  const [followStatus, setFollowStatus] = useState(null);
  const [isOwnProfile, setIsOwnProfile] = useState(true);

  // Load profile data
  const loadProfile = async () => {
    try {
      setLoading(true);
      let response;

      if (username && username !== user?.username) {
        // Viewing another user's profile
        const userResponse = await getUserByUsername(username);
        response = userResponse;
        setIsOwnProfile(false);
      } else {
        // Viewing own profile
        response = await getUserProfile();
        setIsOwnProfile(true);
        editForm.setFieldsValue(response.data);
      }

      setProfileData(response.data);
    } catch (error) {
      message.error('加载用户资料失败');
      console.error('Load profile error:', error);
      if (username && username !== user?.username) {
        navigate('/community'); // Go to community page if other user not found
      } else {
        navigate(`/${user?.username}`); // Go to own profile if own profile fails
      }
    } finally {
      setLoading(false);
    }
  };

  // Load follow status
  const loadFollowStatus = async () => {
    if (!isOwnProfile && profileData) {
      try {
        const response = await getFollowStatus(profileData.id);
        setFollowStatus(response.data);
      } catch (error) {
        console.error('Load follow status error:', error);
      }
    }
  };

  // Handle follow/unfollow
  const handleFollow = async () => {
    if (!profileData) return;

    try {
      const response = await followUser(profileData.id);
      message.success(response.data.message);

      // Update follow status
      setFollowStatus(prev => ({
        ...prev,
        is_following: !prev?.is_following
      }));

      // Reload stats to update follower count
      loadStats();
    } catch (error) {
      message.error('操作失败');
      console.error('Follow error:', error);
    }
  };

  // Load enhanced stats
  const loadStats = async () => {
    try {
      let response;
      if (isOwnProfile) {
        response = await getUserEnhancedStats();
      } else if (profileData) {
        response = await getUserPublicStats(profileData.id);
      } else {
        return; // Don't load stats if we don't have profile data
      }
      setStatsData(response.data);
    } catch (error) {
      console.error('Load stats error:', error);
    }
  };

  // Load activity logs
  const loadActivityLogs = async () => {
    try {
      const response = await getUserActivityLogs({ page: 1, page_size: 10 });
      setActivityLogs(response.data.logs || []);
    } catch (error) {
      console.error('Load activity logs error:', error);
    }
  };

  // Load available environments
  const loadAvailableEnvironments = async () => {
    try {
      const response = await getAvailableEnvironments();
      setAvailableEnvs(response.data.environments || []);
    } catch (error) {
      console.error('Load environments error:', error);
    }
  };

  useEffect(() => {
    loadProfile();
    loadAvailableEnvironments();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [username]);

  useEffect(() => {
    if (profileData) {
      loadStats();
      if (!isOwnProfile) {
        loadFollowStatus();
      } else {
        loadActivityLogs();
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [profileData, isOwnProfile]);

  // Handle profile update
  const handleUpdateProfile = async (values) => {
    try {
      setLoading(true);
      await updateUserProfile(values);
      message.success('个人资料更新成功！');
      setEditMode(false);
      loadProfile();
    } catch (error) {
      message.error('更新失败');
      console.error('Update profile error:', error);
    } finally {
      setLoading(false);
    }
  };

  // Handle avatar upload
  const handleAvatarUpload = async (file) => {
    const isImage = file.type.startsWith('image/');
    if (!isImage) {
      message.error('只能上传图片文件！');
      return false;
    }

    const isLt5M = file.size / 1024 / 1024 < 5;
    if (!isLt5M) {
      message.error('图片大小不能超过5MB！');
      return false;
    }

    try {
      setUploading(true);
      await uploadAvatar(file);
      message.success('头像上传成功！');
      loadProfile();
    } catch (error) {
      message.error('头像上传失败');
      console.error('Avatar upload error:', error);
    } finally {
      setUploading(false);
    }

    return false; // Prevent default upload behavior
  };

  // Handle delete avatar
  const handleDeleteAvatar = async () => {
    try {
      await deleteAvatar();
      message.success('头像删除成功！');
      loadProfile();
    } catch (error) {
      message.error('头像删除失败');
      console.error('Delete avatar error:', error);
    }
  };

  // Handle save code to library
  const handleSaveCode = async (values) => {
    try {
      const response = await saveCodeToLibraryFromShare({
        source_code_id: selectedCode.id,
        title: values.title,
        description: values.description,
        conda_env: values.conda_env
      });
      message.success(response.data.message);
      setSaveCodeModal(false);
      setSelectedCode(null);
      saveCodeForm.resetFields();
    } catch (error) {
      message.error(error.response?.data?.detail || '保存失败');
      console.error('Save code error:', error);
    }
  };

  // Open save code modal
  const openSaveCodeModal = (code) => {
    setSelectedCode(code);
    saveCodeForm.setFieldsValue({
      title: `[Copy] ${code.title}`,
      description: code.description,
      conda_env: 'base'
    });
    setSaveCodeModal(true);
  };

  // Format activity logs
  const formatLogDetails = (details) => {
    if (!details) return '';

    // If details is already an object, stringify it
    if (typeof details === 'object') {
      return JSON.stringify(details, null, 2);
    }

    // If details is a string, try to parse it as JSON
    try {
      const parsed = JSON.parse(details);
      return JSON.stringify(parsed, null, 2);
    } catch {
      // If parsing fails, return the original string
      return details;
    }
  };

  if (loading) {
    return (
      <div style={{ padding: '24px', textAlign: 'center' }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!profileData) {
    return (
      <div style={{ padding: '24px', textAlign: 'center' }}>
        <Empty description="无法加载个人资料" />
      </div>
    );
  }

  return (
    <div style={{ padding: '24px', maxWidth: '1400px', margin: '0 auto' }}>
      <Row gutter={[24, 24]}>
        {/* Left Sidebar - Personal Info */}
        <Col span={8}>
          {/* Profile Card */}
          <Card
            style={{
              marginBottom: '24px',
              background: '#fff',
              border: '1px solid #f0f0f0',
              boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
              borderRadius: '8px'
            }}
          >
            {/* Header Section with Avatar and Basic Info */}
            <div style={{
              display: 'flex',
              alignItems: 'flex-start',
              padding: '24px',
              borderBottom: '1px solid #f0f0f0'
            }}>
              {/* Avatar Section */}
              <div style={{
                position: 'relative',
                marginRight: '20px'
              }}>
                <Avatar
                  size={80}
                  src={profileData.avatar_url ? getAvatarUrl(profileData.avatar_url.split('/').pop()) : null}
                  icon={<UserOutlined />}
                  style={{
                    border: '2px solid #f0f0f0',
                    background: '#fafafa'
                  }}
                />
                {/* Edit Avatar Button - Only for own profile */}
                {isOwnProfile && (
                  <Upload
                    showUploadList={false}
                    beforeUpload={handleAvatarUpload}
                    accept="image/*"
                  >
                    <Button
                      icon={<UploadOutlined />}
                      size="small"
                      loading={uploading}
                      style={{
                        position: 'absolute',
                        bottom: '-4px',
                        right: '-4px',
                        borderRadius: '50%',
                        width: '24px',
                        height: '24px',
                        border: '1px solid #fff',
                        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '10px'
                      }}
                    />
                  </Upload>
                )}
              </div>

              {/* Basic Info Section */}
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
                  <Title
                    level={3}
                    style={{
                      margin: 0,
                      fontSize: '20px',
                      fontWeight: '600',
                      color: '#262626'
                    }}
                  >
                    {profileData.full_name || profileData.username}
                  </Title>
                  {isOwnProfile ? (
                    <Button
                      type="text"
                      icon={editMode ? <SaveOutlined /> : <EditOutlined />}
                      onClick={() => {
                        if (editMode) {
                          editForm.submit();
                        } else {
                          setEditMode(true);
                        }
                      }}
                      style={{
                        color: '#1890ff',
                        fontSize: '14px',
                        height: '32px',
                        padding: '0 8px'
                      }}
                    >
                      {editMode ? '保存' : '编辑'}
                    </Button>
                  ) : (
                    <Button
                      type={followStatus?.is_following ? 'default' : 'primary'}
                      icon={followStatus?.is_following ? <UserDeleteOutlined /> : <UserAddOutlined />}
                      onClick={handleFollow}
                      style={{
                        fontSize: '14px',
                        height: '32px',
                        padding: '0 12px'
                      }}
                    >
                      {followStatus?.is_following ? '已关注' : '关注'}
                    </Button>
                  )}
                </div>
                <Text
                  style={{
                    fontSize: '14px',
                    color: '#8c8c8c',
                    display: 'block',
                    marginBottom: '12px'
                  }}
                >
                  @{profileData.username}
                </Text>

                {/* Bio */}
                {profileData.bio && (
                  <Paragraph
                    style={{
                      margin: '0 0 12px 0',
                      fontSize: '14px',
                      color: '#595959',
                      lineHeight: '1.5'
                    }}
                  >
                    {profileData.bio}
                  </Paragraph>
                )}

                {/* Location and Company */}
                <Space size="small" wrap>
                  {profileData.location && (
                    <span style={{ fontSize: '13px', color: '#8c8c8c' }}>
                      📍 {profileData.location}
                    </span>
                  )}
                  {profileData.company && (
                    <span style={{ fontSize: '13px', color: '#8c8c8c' }}>
                      🏢 {profileData.company}
                    </span>
                  )}
                </Space>
              </div>
            </div>

            {/* Links Section */}
            <div style={{
              padding: '16px 24px',
              borderBottom: '1px solid #f0f0f0'
            }}>
              <Row gutter={[12, 8]}>
                {profileData.github_username && (
                  <Col>
                    <Button
                      type="link"
                      href={`https://github.com/${profileData.github_username}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{
                        padding: '4px 12px',
                        height: 'auto',
                        fontSize: '13px',
                        color: '#1890ff'
                      }}
                    >
                      <span style={{ marginRight: '4px' }}>⚡</span>
                      {profileData.github_username}
                    </Button>
                  </Col>
                )}
                {profileData.website && (
                  <Col>
                    <Button
                      type="link"
                      href={profileData.website}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{
                        padding: '4px 12px',
                        height: 'auto',
                        fontSize: '13px',
                        color: '#1890ff'
                      }}
                    >
                      🌐 个人网站
                    </Button>
                  </Col>
                )}
                {isOwnProfile && profileData.avatar_url && (
                  <Col>
                    <Button
                      type="text"
                      icon={<EditOutlined />}
                      onClick={handleDeleteAvatar}
                      style={{
                        padding: '4px 12px',
                        height: 'auto',
                        fontSize: '13px',
                        color: '#ff4d4f'
                      }}
                    >
                      删除头像
                    </Button>
                  </Col>
                )}
              </Row>
            </div>

            {/* Edit Form - Only for own profile */}
            {isOwnProfile && editMode && (
              <div style={{ marginTop: '24px' }}>
                <Form
                  form={editForm}
                  layout="vertical"
                  onFinish={handleUpdateProfile}
                >
                  <Form.Item name="full_name" label="姓名">
                    <Input />
                  </Form.Item>
                  <Form.Item name="location" label="位置">
                    <Input />
                  </Form.Item>
                  <Form.Item name="company" label="公司">
                    <Input />
                  </Form.Item>
                  <Form.Item name="github_username" label="GitHub用户名">
                    <Input />
                  </Form.Item>
                  <Form.Item name="website" label="个人网站">
                    <Input />
                  </Form.Item>
                  <Form.Item name="bio" label="个人简介">
                    <TextArea rows={3} />
                  </Form.Item>
                </Form>
              </div>
            )}
          </Card>

          {/* Statistics */}
          {statsData && (
            <Card title="数据统计" size="small">
              <Row gutter={[8, 8]}>
                <Col span={12}>
                  <Statistic
                    title="代码库"
                    value={statsData.code_library_count}
                    prefix={<BookOutlined />}
                    valueStyle={{ color: '#1890ff', fontSize: '18px' }}
                  />
                </Col>
                <Col span={12}>
                  <Statistic
                    title="帖子"
                    value={statsData.posts_count}
                    prefix={<MessageOutlined />}
                    valueStyle={{ color: '#52c41a', fontSize: '18px' }}
                  />
                </Col>
                <Col span={12}>
                  <div
                    style={{ cursor: 'pointer', padding: '8px', borderRadius: '4px', transition: 'background-color 0.3s' }}
                    onClick={() => navigate(`/${profileData.username}/followers`)}
                    onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f5f5f5'}
                    onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                  >
                    <Statistic
                      title="粉丝"
                      value={statsData.followers_count}
                      prefix={<TeamOutlined />}
                      valueStyle={{ color: '#faad14', fontSize: '18px' }}
                    />
                  </div>
                </Col>
                <Col span={12}>
                  <div
                    style={{ cursor: 'pointer', padding: '8px', borderRadius: '4px', transition: 'background-color 0.3s' }}
                    onClick={() => navigate(`/${profileData.username}/following`)}
                    onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f5f5f5'}
                    onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                  >
                    <Statistic
                      title="关注"
                      value={statsData.following_count}
                      prefix={<UserOutlined />}
                      valueStyle={{ color: '#722ed1', fontSize: '18px' }}
                    />
                  </div>
                </Col>
              </Row>
              <Divider style={{ margin: '16px 0' }} />
              <Row gutter={[8, 8]}>
                <Col span={8}>
                  <Statistic
                    title="总点赞"
                    value={statsData.total_likes}
                    prefix={<HeartOutlined />}
                    valueStyle={{ color: '#ff4d4f', fontSize: '16px' }}
                  />
                </Col>
                <Col span={8}>
                  <Statistic
                    title="总收藏"
                    value={statsData.total_favorites}
                    prefix={<StarOutlined />}
                    valueStyle={{ color: '#fa8c16', fontSize: '16px' }}
                  />
                </Col>
                <Col span={8}>
                  <Statistic
                    title="总浏览"
                    value={statsData.total_views}
                    prefix={<EyeOutlined />}
                    valueStyle={{ color: '#13c2c2', fontSize: '16px' }}
                  />
                </Col>
              </Row>
            </Card>
          )}
        </Col>

        {/* Right Content - Tabs */}
        <Col span={16}>
          <Card>
            <Tabs defaultActiveKey="1" size="large">
              <TabPane tab={<span><CodeOutlined />最近代码</span>} key="1">
                {statsData?.recent_codes?.length > 0 ? (
                  <List
                    dataSource={statsData.recent_codes}
                    renderItem={(code) => (
                      <List.Item
                        actions={[
                          <Button
                            type="link"
                            icon={<DownloadOutlined />}
                            onClick={() => openSaveCodeModal(code)}
                          >
                            转存
                          </Button>
                        ]}
                      >
                        <List.Item.Meta
                          title={code.title}
                          description={
                            <div>
                              <Text type="secondary">{code.description}</Text>
                              <br />
                              <Space>
                                <Tag>{code.language}</Tag>
                                <Tag color="blue">{code.conda_env}</Tag>
                                <Text type="secondary" style={{ fontSize: '12px' }}>
                                  {moment(code.created_at).fromNow()}
                                </Text>
                              </Space>
                            </div>
                          }
                        />
                      </List.Item>
                    )}
                  />
                ) : (
                  <Empty description="暂无代码库" />
                )}
              </TabPane>

              <TabPane tab={<span><MessageOutlined />最近帖子</span>} key="2">
                {statsData?.recent_posts?.length > 0 ? (
                  <List
                    dataSource={statsData.recent_posts}
                    renderItem={(post) => (
                      <List.Item>
                        <List.Item.Meta
                          title={
                            <a href={`/community/post/${post.id}`} target="_blank" rel="noopener noreferrer">
                              {post.title}
                            </a>
                          }
                          description={
                            <div>
                              <Text type="secondary">{post.summary}</Text>
                              <br />
                              <Space>
                                <Tag color="blue">{moment(post.created_at).format('YYYY-MM-DD')}</Tag>
                                <Space size="small">
                                  <HeartOutlined style={{ color: '#ff4d4f' }} />
                                  <Text style={{ fontSize: '12px' }}>{post.like_count}</Text>
                                </Space>
                                <Space size="small">
                                  <MessageOutlined style={{ color: '#1890ff' }} />
                                  <Text style={{ fontSize: '12px' }}>{post.comment_count}</Text>
                                </Space>
                                <Space size="small">
                                  <EyeOutlined style={{ color: '#52c41a' }} />
                                  <Text style={{ fontSize: '12px' }}>{post.view_count}</Text>
                                </Space>
                              </Space>
                            </div>
                          }
                        />
                      </List.Item>
                    )}
                  />
                ) : (
                  <Empty description="暂无帖子" />
                )}
              </TabPane>

              <TabPane tab={<span><StarOutlined />收藏帖子</span>} key="3">
                {statsData?.favorite_posts?.length > 0 ? (
                  <List
                    dataSource={statsData.favorite_posts}
                    renderItem={(post) => (
                      <List.Item>
                        <List.Item.Meta
                          title={
                            <a href={`/community/post/${post.id}`} target="_blank" rel="noopener noreferrer">
                              {post.title}
                            </a>
                          }
                          description={
                            <div>
                              <Text type="secondary">作者: {post.author_full_name || post.author_username}</Text>
                              <br />
                              <Tag color="orange">{moment(post.created_at).format('YYYY-MM-DD')}</Tag>
                            </div>
                          }
                        />
                      </List.Item>
                    )}
                  />
                ) : (
                  <Empty description="暂无收藏" />
                )}
              </TabPane>

              <TabPane tab={<span><HeartOutlined />点赞帖子</span>} key="4">
                {statsData?.liked_posts?.length > 0 ? (
                  <List
                    dataSource={statsData.liked_posts}
                    renderItem={(post) => (
                      <List.Item>
                        <List.Item.Meta
                          title={
                            <a href={`/community/post/${post.id}`} target="_blank" rel="noopener noreferrer">
                              {post.title}
                            </a>
                          }
                          description={
                            <div>
                              <Text type="secondary">作者: {post.author_full_name || post.author_username}</Text>
                              <br />
                              <Tag color="red">{moment(post.created_at).format('YYYY-MM-DD')}</Tag>
                            </div>
                          }
                        />
                      </List.Item>
                    )}
                  />
                ) : (
                  <Empty description="暂无点赞" />
                )}
              </TabPane>

              {isOwnProfile && (
                <TabPane tab={<span><EditOutlined />活动日志</span>} key="5">
                  {activityLogs.length > 0 ? (
                    <List
                      dataSource={activityLogs}
                      renderItem={(log) => (
                        <List.Item>
                          <List.Item.Meta
                            title={
                              <Space>
                                <Text strong>{log.action}</Text>
                                <Tag color={log.status === 'success' ? 'green' : 'red'}>
                                  {log.status}
                                </Tag>
                              </Space>
                            }
                            description={
                              <div>
                                <Text type="secondary">{moment(log.created_at).fromNow()}</Text>
                                <br />
                                {log.resource_type && <Tag>{log.resource_type}</Tag>}
                                {log.details && (
                                  <details style={{ marginTop: '8px' }}>
                                    <summary style={{ cursor: 'pointer' }}>详细信息</summary>
                                    <pre style={{ marginTop: '8px', fontSize: '12px', background: '#f5f5f5', padding: '8px', borderRadius: '4px' }}>
                                      {formatLogDetails(log.details)}
                                    </pre>
                                  </details>
                                )}
                              </div>
                            }
                          />
                        </List.Item>
                      )}
                    />
                  ) : (
                    <Empty description="暂无活动日志" />
                  )}
                </TabPane>
              )}
            </Tabs>
          </Card>
        </Col>
      </Row>

      {/* Save Code Modal */}
      <Modal
        title="转存代码到我的代码库"
        open={saveCodeModal}
        onCancel={() => {
          setSaveCodeModal(false);
          setSelectedCode(null);
          saveCodeForm.resetFields();
        }}
        onOk={() => saveCodeForm.submit()}
        okText="转存"
        cancelText="取消"
      >
        <Form
          form={saveCodeForm}
          layout="vertical"
          onFinish={handleSaveCode}
        >
          <Form.Item
            name="title"
            label="代码标题"
            rules={[{ required: true, message: '请输入代码标题' }]}
          >
            <Input />
          </Form.Item>
          <Form.Item name="description" label="代码描述">
            <TextArea rows={3} />
          </Form.Item>
          <Form.Item
            name="conda_env"
            label="运行环境"
            rules={[{ required: true, message: '请选择运行环境' }]}
          >
            <Select>
              {availableEnvs.map((env) => (
                <Option key={env.name} value={env.name}>
                  {env.display_name} {env.is_default && '(默认)'}
                </Option>
              ))}
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default ProfilePage;