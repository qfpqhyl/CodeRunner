import React, { useState, useEffect } from 'react';
import {
  Card,
  List,
  Avatar,
  Button,
  Spin,
  Empty,
  Typography,
  Pagination,
  Row,
  Col,
  Space,
  message
} from 'antd';
import {
  UserOutlined,
  TeamOutlined,
  UserAddOutlined,
  UserDeleteOutlined
} from '@ant-design/icons';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../components/AuthContext';
import moment from 'moment';
import {
  getUserFollowers,
  getUserFollowing,
  getFollowStatus,
  followUser,
  getUserByUsername
} from '../services/api';

const { Title, Text } = Typography;

const FollowListPage = () => {
  const { username, type } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 20,
    total: 0
  });
  const [profileInfo, setProfileInfo] = useState(null);
  const [followStatuses, setFollowStatuses] = useState({});

  // Load profile info
  const loadProfileInfo = async () => {
    try {
      const response = await getUserByUsername(username);
      setProfileInfo(response.data);
    } catch (error) {
      message.error('用户不存在');
      console.error('Load profile info error:', error);
      navigate('/profile');
    }
  };

  // Load follow data
  const loadFollowData = async (page = 1) => {
    if (!profileInfo) return;

    try {
      setLoading(true);
      const params = { page, page_size: pagination.pageSize };
      const apiCall = type === 'followers' ? getUserFollowers : getUserFollowing;
      const response = await apiCall(profileInfo.id, params);

      const listKey = type === 'followers' ? 'followers' : 'following';
      setData(response.data[listKey] || []);
      setPagination({
        current: response.data.pagination.current_page,
        pageSize: response.data.pagination.page_size,
        total: response.data.pagination.total_count
      });

      // Load follow statuses for each user
      if (user && user.id !== profileInfo.id) {
        const statuses = {};
        for (const item of response.data[listKey] || []) {
          try {
            const statusResponse = await getFollowStatus(item.id);
            statuses[item.id] = statusResponse.data;
          } catch (error) {
            console.error('Load follow status error:', error);
          }
        }
        setFollowStatuses(statuses);
      }
    } catch (error) {
      message.error('加载关注列表失败');
      console.error('Load follow data error:', error);
    } finally {
      setLoading(false);
    }
  };

  // Handle follow/unfollow
  const handleFollow = async (userId) => {
    try {
      const response = await followUser(userId);
      message.success(response.data.message);

      // Update follow status
      setFollowStatuses(prev => ({
        ...prev,
        [userId]: { is_following: !prev[userId]?.is_following, is_self: false }
      }));

      // Refresh data
      loadFollowData(pagination.current);
    } catch (error) {
      message.error('操作失败');
      console.error('Follow error:', error);
    }
  };

  useEffect(() => {
    loadProfileInfo();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [username]);

  useEffect(() => {
    if (profileInfo) {
      loadFollowData();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [profileInfo, type]);

  const handlePageChange = (page, pageSize) => {
    setPagination(prev => ({ ...prev, current: page, pageSize }));
    loadFollowData(page);
  };

  if (loading && !profileInfo) {
    return (
      <div style={{ padding: '24px', textAlign: 'center' }}>
        <Spin size="large" />
      </div>
    );
  }

  const pageTitle = type === 'followers' ? '粉丝' : '关注';
  const pageIcon = type === 'followers' ? <TeamOutlined /> : <UserOutlined />;

  return (
    <div style={{ padding: '24px', maxWidth: '800px', margin: '0 auto' }}>
      {/* Header */}
      <Card style={{ marginBottom: '24px' }}>
        <Row align="middle" justify="space-between">
          <Col>
            <Space>
              <Button
                type="text"
                onClick={() => navigate(`/profile/${username}`)}
                style={{ fontSize: '16px' }}
              >
                ← 返回
              </Button>
              <Title level={3} style={{ margin: 0, display: 'flex', alignItems: 'center' }}>
                {pageIcon}
                <span style={{ marginLeft: '8px' }}>
                  {profileInfo?.full_name || profileInfo?.username}的{pageTitle}
                </span>
              </Title>
              <Text type="secondary" style={{ marginLeft: '16px' }}>
                共 {pagination.total} 位{pageTitle}
              </Text>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* User List */}
      <Card>
        <List
          loading={loading}
          dataSource={data}
          renderItem={(item) => (
            <List.Item
              actions={
                user && user.id !== item.id ? (
                  <Button
                    type={followStatuses[item.id]?.is_following ? 'default' : 'primary'}
                    icon={followStatuses[item.id]?.is_following ? <UserDeleteOutlined /> : <UserAddOutlined />}
                    onClick={() => handleFollow(item.id)}
                    loading={false}
                  >
                    {followStatuses[item.id]?.is_following ? '已关注' : '关注'}
                  </Button>
                ) : null
              }
            >
              <List.Item.Meta
                avatar={
                  <Avatar
                    size={48}
                    src={item.avatar_url}
                    icon={<UserOutlined />}
                  />
                }
                title={
                  <Space>
                    <Button
                      type="link"
                      onClick={() => navigate(`/profile/${item.username}`)}
                      style={{ padding: 0, fontSize: '16px', fontWeight: '500' }}
                    >
                      {item.full_name || item.username}
                    </Button>
                    {item.full_name && (
                      <Text type="secondary">@{item.username}</Text>
                    )}
                  </Space>
                }
                description={
                  <Space>
                    <Text type="secondary">
                      {moment(item.followed_at).format('YYYY-MM-DD HH:mm')}
                    </Text>
                  </Space>
                }
              />
            </List.Item>
          )}
          locale={{
            emptyText: (
              <Empty
                description={`暂无${pageTitle}`}
                image={Empty.PRESENTED_IMAGE_SIMPLE}
              />
            )
          }}
        />

        {/* Pagination */}
        {data.length > 0 && (
          <div style={{ textAlign: 'center', marginTop: '24px' }}>
            <Pagination
              current={pagination.current}
              pageSize={pagination.pageSize}
              total={pagination.total}
              onChange={handlePageChange}
              showSizeChanger
              showQuickJumper
              showTotal={(total, range) =>
                `第 ${range[0]}-${range[1]} 条，共 ${total} 条`
              }
            />
          </div>
        )}
      </Card>
    </div>
  );
};

export default FollowListPage;