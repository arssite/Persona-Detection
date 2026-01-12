import React from 'react';
import { Card, CardContent, Typography, Avatar, Box, Chip } from '@mui/material';
import { X as XIcon, Verified, LocationOn, Language, CalendarToday } from '@mui/icons-material';

interface XProfileData {
  username: string;
  url: string;
  name?: string;
  bio?: string;
  followers_count?: number;
  following_count?: number;
  tweets_count?: number;
  is_verified?: boolean;
  location?: string;
  website?: string;
  joined_date?: string;
}

interface XCardProps {
  profile: XProfileData;
}

const XCard: React.FC<XCardProps> = ({ profile }) => {
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
        background: 'linear-gradient(135deg, #000000 0%, #14171a 100%)',
        color: 'white',
        transition: 'transform 0.2s',
        '&:hover': {
          transform: 'translateY(-4px)',
        },
      }}
    >
      <CardContent>
        <Box display="flex" alignItems="center" gap={2} mb={2}>
          <Box
            sx={{
              width: 32,
              height: 32,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <svg viewBox="0 0 24 24" width="28" height="28" fill="white">
              <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
            </svg>
          </Box>
          <Typography variant="h6" fontWeight="bold">
            X / Twitter Profile
          </Typography>
        </Box>

        <Box display="flex" alignItems="center" gap={2} mb={2}>
          <Avatar
            alt={profile.username}
            sx={{ width: 64, height: 64, border: '3px solid #1DA1F2', bgcolor: '#1DA1F2' }}
          >
            {profile.username[0]?.toUpperCase()}
          </Avatar>
          <Box flex={1}>
            <Box display="flex" alignItems="center" gap={1}>
              <Typography variant="h6" fontWeight="bold">
                {profile.name || `@${profile.username}`}
              </Typography>
              {profile.is_verified && (
                <Verified sx={{ fontSize: 20, color: '#1DA1F2' }} />
              )}
            </Box>
            <Typography variant="body2" sx={{ opacity: 0.7 }}>
              @{profile.username}
            </Typography>
          </Box>
        </Box>

        {profile.bio && (
          <Typography
            variant="body2"
            sx={{
              mb: 2,
              opacity: 0.9,
              whiteSpace: 'pre-wrap',
            }}
          >
            {profile.bio}
          </Typography>
        )}

        <Box display="flex" flexDirection="column" gap={1} mb={2}>
          {profile.location && (
            <Box display="flex" alignItems="center" gap={1}>
              <LocationOn sx={{ fontSize: 18, opacity: 0.7 }} />
              <Typography variant="body2" sx={{ opacity: 0.8 }}>
                {profile.location}
              </Typography>
            </Box>
          )}
          {profile.website && (
            <Box display="flex" alignItems="center" gap={1}>
              <Language sx={{ fontSize: 18, opacity: 0.7 }} />
              <Typography
                variant="body2"
                component="a"
                href={profile.website}
                target="_blank"
                rel="noopener noreferrer"
                sx={{ opacity: 0.8, color: '#1DA1F2', textDecoration: 'none' }}
              >
                {profile.website}
              </Typography>
            </Box>
          )}
          {profile.joined_date && (
            <Box display="flex" alignItems="center" gap={1}>
              <CalendarToday sx={{ fontSize: 18, opacity: 0.7 }} />
              <Typography variant="body2" sx={{ opacity: 0.8 }}>
                Joined {profile.joined_date}
              </Typography>
            </Box>
          )}
        </Box>

        <Box display="flex" gap={3} mb={2}>
          <Box>
            <Typography variant="h6" fontWeight="bold">
              {formatCount(profile.tweets_count)}
            </Typography>
            <Typography variant="caption" sx={{ opacity: 0.7 }}>
              Posts
            </Typography>
          </Box>
          <Box>
            <Typography variant="h6" fontWeight="bold">
              {formatCount(profile.followers_count)}
            </Typography>
            <Typography variant="caption" sx={{ opacity: 0.7 }}>
              Followers
            </Typography>
          </Box>
          <Box>
            <Typography variant="h6" fontWeight="bold">
              {formatCount(profile.following_count)}
            </Typography>
            <Typography variant="caption" sx={{ opacity: 0.7 }}>
              Following
            </Typography>
          </Box>
        </Box>

        <Box display="flex" gap={1} flexWrap="wrap">
          <Chip
            label="View Profile"
            size="small"
            component="a"
            href={profile.url}
            target="_blank"
            rel="noopener noreferrer"
            clickable
            sx={{
              bgcolor: '#1DA1F2',
              color: 'white',
              fontWeight: 'bold',
              '&:hover': {
                bgcolor: '#1a91da',
              },
            }}
          />
        </Box>
      </CardContent>
    </Card>
  );
};

export default XCard;
