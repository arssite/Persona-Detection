import React from 'react';
import { Card, CardContent, Typography, Avatar, Box, Chip } from '@mui/material';
import { Instagram, Verified, Lock } from '@mui/icons-material';

interface InstagramProfileData {
  username: string;
  url: string;
  full_name?: string;
  bio?: string;
  followers_count?: number;
  following_count?: number;
  posts_count?: number;
  is_verified?: boolean;
  profile_pic_url?: string;
  is_private?: boolean;
}

interface InstagramCardProps {
  profile: InstagramProfileData;
}

const InstagramCard: React.FC<InstagramCardProps> = ({ profile }) => {
  const formatCount = (count?: number) => {
    if (!count) return '—';
    if (count >= 1000000) {
      return `${(count / 1000000).toFixed(1)}M`;
    }
    if (count >= 1000) {
      return `${(count / 1000).toFixed(1)}K`;
    }
    return count.toLocaleString();
  };

  return (
    <Card
      sx={{
        background: 'linear-gradient(45deg, #f09433 0%, #e6683c 25%, #dc2743 50%, #cc2366 75%, #bc1888 100%)',
        color: 'white',
        transition: 'transform 0.2s',
        '&:hover': {
          transform: 'translateY(-4px)',
        },
      }}
    >
      <CardContent>
        <Box display="flex" alignItems="center" gap={2} mb={2}>
          <Instagram sx={{ fontSize: 32 }} />
          <Typography variant="h6" fontWeight="bold">
            Instagram Profile
          </Typography>
        </Box>

        <Box display="flex" alignItems="center" gap={2} mb={2}>
          <Avatar
            src={profile.profile_pic_url || undefined}
            alt={profile.username}
            sx={{ width: 64, height: 64, border: '3px solid white' }}
          >
            {profile.username[0]?.toUpperCase()}
          </Avatar>
          <Box flex={1}>
            <Box display="flex" alignItems="center" gap={1}>
              <Typography variant="h6" fontWeight="bold">
                {profile.full_name || `@${profile.username}`}
              </Typography>
              {profile.is_verified && (
                <Verified sx={{ fontSize: 20, color: '#3897f0' }} />
              )}
              {profile.is_private && (
                <Lock sx={{ fontSize: 18, opacity: 0.8 }} />
              )}
            </Box>
            {profile.full_name && (
              <Typography variant="body2" sx={{ opacity: 0.9 }}>
                @{profile.username}
              </Typography>
            )}
          </Box>
        </Box>

        {profile.bio && (
          <Typography
            variant="body2"
            sx={{
              mb: 2,
              opacity: 0.95,
              fontStyle: 'italic',
              whiteSpace: 'pre-wrap',
            }}
          >
            "{profile.bio}"
          </Typography>
        )}

        <Box display="flex" gap={2} flexWrap="wrap" mb={2}>
          <Box textAlign="center">
            <Typography variant="h6" fontWeight="bold">
              {formatCount(profile.posts_count)}
            </Typography>
            <Typography variant="caption" sx={{ opacity: 0.9 }}>
              Posts
            </Typography>
          </Box>
          <Box textAlign="center">
            <Typography variant="h6" fontWeight="bold">
              {formatCount(profile.followers_count)}
            </Typography>
            <Typography variant="caption" sx={{ opacity: 0.9 }}>
              Followers
            </Typography>
          </Box>
          <Box textAlign="center">
            <Typography variant="h6" fontWeight="bold">
              {formatCount(profile.following_count)}
            </Typography>
            <Typography variant="caption" sx={{ opacity: 0.9 }}>
              Following
            </Typography>
          </Box>
        </Box>

        <Box display="flex" gap={1} flexWrap="wrap">
          {profile.is_private && (
            <Chip
              label="Private Account"
              size="small"
              icon={<Lock />}
              sx={{
                bgcolor: 'rgba(255, 255, 255, 0.2)',
                color: 'white',
              }}
            />
          )}
          <Chip
            label="View Profile"
            size="small"
            component="a"
            href={profile.url}
            target="_blank"
            rel="noopener noreferrer"
            clickable
            sx={{
              bgcolor: 'rgba(255, 255, 255, 0.9)',
              color: '#e1306c',
              fontWeight: 'bold',
              '&:hover': {
                bgcolor: 'white',
              },
            }}
          />
        </Box>
      </CardContent>
    </Card>
  );
};

export default InstagramCard;
