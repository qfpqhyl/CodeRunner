import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Button,
  Input,
  Select,
  Tag,
  Avatar,
  message,
  Spin,
  Empty,
  Space,
  Typography,
  Tooltip,
  Pagination
} from 'antd';
import {
  PlusOutlined,
  HeartOutlined,
  MessageOutlined,
  StarOutlined,
  EyeOutlined,
  UserOutlined,
  ShareAltOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import moment from 'moment';
import {
  getPosts,
  likePost,
  favoritePost,
  followUser
} from '../services/api';

const { Title, Text, Paragraph } = Typography;
const { Search } = Input;
const { Option } = Select;

const CommunityPage = () => {
  const navigate = useNavigate();
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 12,
    total: 0
  });
  const [filters, setFilters] = useState({
    search: '',
    tag: '',
    sort_by: 'latest',
    author_id: null
  });

  // Load posts
  const loadPosts = async (params = {}) => {
    try {
      setLoading(true);
      const queryParams = {
        page: params.page || pagination.current,
        page_size: params.pageSize || pagination.pageSize,
        ...filters
      };

      const response = await getPosts(queryParams);
      setPosts(response.data.posts);
      setPagination({
        current: response.data.pagination.current_page,
        pageSize: response.data.pagination.page_size,
        total: response.data.pagination.total_count
      });
    } catch (error) {
      message.error('加载帖子失败');
      console.error('Load posts error:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPosts();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Handle search
  const handleSearch = (value) => {
    setFilters({ ...filters, search: value });
    setPagination({ ...pagination, current: 1 });
    loadPosts({ page: 1 });
  };

  // Handle filter change
  const handleFilterChange = (key, value) => {
    const newFilters = { ...filters, [key]: value };
    setFilters(newFilters);
    setPagination({ ...pagination, current: 1 });
    loadPosts({ page: 1, ...newFilters });
  };

  // Handle pagination change
  const handlePaginationChange = (page, pageSize) => {
    setPagination({ current: page, pageSize });
    loadPosts({ page, pageSize });
  };

  // Handle like post
  const handleLikePost = async (postId) => {
    try {
      const response = await likePost(postId);

      // Update post in local state
      setPosts(posts.map(post => {
        if (post.id === postId) {
          return {
            ...post,
            like_count: response.data.like_count,
            is_liked_by_current_user: response.data.is_liked
          };
        }
        return post;
      }));

      message.success(response.data.message);
    } catch (error) {
      message.error('操作失败');
      console.error('Like post error:', error);
    }
  };

  // Handle favorite post
  const handleFavoritePost = async (postId) => {
    try {
      const response = await favoritePost(postId);

      // Update post in local state
      setPosts(posts.map(post => {
        if (post.id === postId) {
          return {
            ...post,
            favorite_count: response.data.favorite_count,
            is_favorited_by_current_user: response.data.is_favorited
          };
        }
        return post;
      }));

      message.success(response.data.message);
    } catch (error) {
      message.error('操作失败');
      console.error('Favorite post error:', error);
    }
  };

  // Handle follow user
  const handleFollowUser = async (userId, username) => {
    try {
      const response = await followUser(userId);
      message.success(response.data.message);
    } catch (error) {
      message.error('操作失败');
      console.error('Follow user error:', error);
    }
  };

  // Handle create post
  const handleCreatePost = () => {
    navigate('/community/create');
  };

  // Handle view post
  const handleViewPost = (postId) => {
    navigate(`/community/post/${postId}`);
  };

  // Format tags
  const formatTags = (tags) => {
    if (!tags) return [];
    return tags.split(',').map(tag => tag.trim()).filter(tag => tag);
  };

  // Get popular tags from posts
  const getPopularTags = () => {
    const tagCounts = {};
    posts.forEach(post => {
      const tags = formatTags(post.tags);
      tags.forEach(tag => {
        tagCounts[tag] = (tagCounts[tag] || 0) + 1;
      });
    });
    return Object.entries(tagCounts)
      .sort(([,a], [,b]) => b - a)
      .slice(0, 10)
      .map(([tag, count]) => ({ tag, count }));
  };

  const popularTags = getPopularTags();

  return (
    <div style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={2}>社区广场</Title>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={handleCreatePost}
        >
          发布帖子
        </Button>
      </div>

      <Row gutter={[24, 24]}>
        {/* Sidebar */}
        <Col span={6}>
          {/* Search */}
          <Card title="搜索" style={{ marginBottom: '16px' }}>
            <Search
              placeholder="搜索帖子..."
              allowClear
              onSearch={handleSearch}
              onChange={(e) => handleSearch(e.target.value)}
            />
          </Card>

          {/* Filters */}
          <Card title="筛选" style={{ marginBottom: '16px' }}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <div>
                <Text strong>排序方式：</Text>
                <Select
                  value={filters.sort_by}
                  onChange={(value) => handleFilterChange('sort_by', value)}
                  style={{ width: '100%', marginTop: '8px' }}
                >
                  <Option value="latest">最新发布</Option>
                  <Option value="popular">最热门</Option>
                  <Option value="most_liked">最多点赞</Option>
                  <Option value="most_commented">最多评论</Option>
                </Select>
              </div>

              {popularTags.length > 0 && (
                <div>
                  <Text strong>热门标签：</Text>
                  <div style={{ marginTop: '8px' }}>
                    {popularTags.map(({ tag, count }) => (
                      <Tag
                        key={tag}
                        color={filters.tag === tag ? 'blue' : 'default'}
                        style={{ cursor: 'pointer', marginBottom: '4px' }}
                        onClick={() => handleFilterChange('tag', filters.tag === tag ? '' : tag)}
                      >
                        {tag} ({count})
                      </Tag>
                    ))}
                  </div>
                </div>
              )}
            </Space>
          </Card>

          {/* Statistics */}
          <Card title="统计信息">
            <Space direction="vertical" style={{ width: '100%' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <Text>总帖子数：</Text>
                <Text strong>{pagination.total}</Text>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <Text>当前页：</Text>
                <Text strong>{pagination.current}/{Math.ceil(pagination.total / pagination.pageSize)}</Text>
              </div>
            </Space>
          </Card>
        </Col>

        {/* Posts List */}
        <Col span={18}>
          <Spin spinning={loading}>
            {posts.length === 0 && !loading ? (
              <Empty
                description="暂无帖子，快来发布第一个帖子吧！"
                image={Empty.PRESENTED_IMAGE_SIMPLE}
              >
                <Button type="primary" icon={<PlusOutlined />} onClick={handleCreatePost}>
                  发布帖子
                </Button>
              </Empty>
            ) : (
              <>
                <Row gutter={[16, 16]}>
                  {posts.map((post) => (
                    <Col span={24} key={post.id}>
                      <Card
                        hoverable
                        style={{
                          cursor: 'pointer',
                          borderRadius: '8px',
                          boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
                          transition: 'all 0.3s ease'
                        }}
                        bodyStyle={{ padding: '20px' }}
                        onClick={() => handleViewPost(post.id)}
                        actions={[
                          <Tooltip title="查看详情">
                            <EyeOutlined key="view" style={{ fontSize: '16px' }} />
                          </Tooltip>,
                          <Tooltip title={post.is_liked_by_current_user ? "取消点赞" : "点赞"}>
                            <HeartOutlined
                              key="like"
                              style={{
                                color: post.is_liked_by_current_user ? '#ff4d4f' : 'inherit',
                                fontSize: '16px'
                              }}
                              onClick={(e) => {
                                e.stopPropagation();
                                handleLikePost(post.id);
                              }}
                            />
                          </Tooltip>,
                          <Tooltip title={post.is_favorited_by_current_user ? "取消收藏" : "收藏"}>
                            <StarOutlined
                              key="favorite"
                              style={{
                                color: post.is_favorited_by_current_user ? '#faad14' : 'inherit',
                                fontSize: '16px'
                              }}
                              onClick={(e) => {
                                e.stopPropagation();
                                handleFavoritePost(post.id);
                              }}
                            />
                          </Tooltip>,
                          <Tooltip title="关注作者">
                            <UserOutlined
                              key="follow"
                              style={{ fontSize: '16px' }}
                              onClick={(e) => {
                                e.stopPropagation();
                                handleFollowUser(post.user_id, post.author_username);
                              }}
                            />
                          </Tooltip>
                        ]}
                      >
                        {/* Post Header */}
                        <div style={{ marginBottom: '12px' }}>
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                            <div style={{ display: 'flex', alignItems: 'center' }}>
                              <Avatar
                                size="small"
                                src={post.author_avatar}
                                icon={<UserOutlined />}
                                style={{ marginRight: '8px' }}
                              />
                              <div>
                                <Text strong>{post.author_full_name || post.author_username}</Text>
                                <br />
                                <Text type="secondary" style={{ fontSize: '12px' }}>
                                  {moment(post.created_at).fromNow()}
                                </Text>
                              </div>
                            </div>
                            {post.is_pinned && (
                              <Tag color="red" icon={<UserOutlined />}>置顶</Tag>
                            )}
                          </div>
                        </div>

                        {/* Post Title */}
                        <Title level={4} style={{ marginBottom: '8px' }}>
                          {post.title}
                        </Title>

                        {/* Post Summary */}
                        {post.summary && (
                          <Paragraph
                            ellipsis={{ rows: 2 }}
                            style={{ marginBottom: '12px', color: '#666' }}
                          >
                            {post.summary}
                          </Paragraph>
                        )}

                        {/* Tags */}
                        {post.tags && (
                          <div style={{ marginBottom: '12px' }}>
                            {formatTags(post.tags).map((tag, index) => (
                              <Tag key={index} style={{ marginBottom: '4px', marginRight: '4px' }}>
                                {tag}
                              </Tag>
                            ))}
                          </div>
                        )}

                        {/* Shared Codes */}
                        {post.shared_codes && post.shared_codes.length > 0 && (
                          <div style={{ marginBottom: '12px' }}>
                            <Text strong>分享的代码：</Text>
                            <div style={{ marginTop: '8px' }}>
                              {post.shared_codes.map((code, index) => (
                                <Tag
                                  key={code.id}
                                  icon={<ShareAltOutlined />}
                                  color="blue"
                                  style={{ marginBottom: '4px', marginRight: '4px' }}
                                >
                                  {code.title}
                                </Tag>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Post Stats */}
                        <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginTop: '12px' }}>
                          <Space split={<span style={{ color: '#d9d9d9' }}>|</span>}>
                            <Space size={4}>
                              <HeartOutlined style={{ color: '#ff4d4f', fontSize: '14px' }} />
                              <Text type="secondary" style={{ fontSize: '12px' }}>{post.like_count}</Text>
                            </Space>
                            <Space size={4}>
                              <MessageOutlined style={{ color: '#1890ff', fontSize: '14px' }} />
                              <Text type="secondary" style={{ fontSize: '12px' }}>{post.comment_count}</Text>
                            </Space>
                            <Space size={4}>
                              <StarOutlined style={{ color: '#faad14', fontSize: '14px' }} />
                              <Text type="secondary" style={{ fontSize: '12px' }}>{post.favorite_count}</Text>
                            </Space>
                            <Space size={4}>
                              <EyeOutlined style={{ color: '#52c41a', fontSize: '14px' }} />
                              <Text type="secondary" style={{ fontSize: '12px' }}>{post.view_count}</Text>
                            </Space>
                          </Space>
                        </div>
                      </Card>
                    </Col>
                  ))}
                </Row>

                {/* Pagination */}
                <div style={{ textAlign: 'center', marginTop: '24px' }}>
                  <Pagination
                    current={pagination.current}
                    pageSize={pagination.pageSize}
                    total={pagination.total}
                    showSizeChanger
                    showQuickJumper
                    showTotal={(total, range) =>
                      `第 ${range[0]}-${range[1]} 条，共 ${total} 条`
                    }
                    onChange={handlePaginationChange}
                    onShowSizeChange={handlePaginationChange}
                  />
                </div>
              </>
            )}
          </Spin>
        </Col>
      </Row>
    </div>
  );
};

export default CommunityPage;