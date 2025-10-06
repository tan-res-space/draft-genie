/**
 * Speaker Response DTO
 */

import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';
import { BucketType, SpeakerStatus } from '../../common/constants/enums';

export class SpeakerResponseDto {
  @ApiProperty({
    description: 'Speaker ID',
    example: '550e8400-e29b-41d4-a716-446655440000',
  })
  id: string;

  @ApiPropertyOptional({
    description: 'External ID from source system',
    example: 'instanote-speaker-12345',
  })
  externalId?: string;

  @ApiProperty({
    description: 'Speaker name',
    example: 'Dr. John Smith',
  })
  name: string;

  @ApiPropertyOptional({
    description: 'Speaker email address',
    example: 'john.smith@hospital.com',
  })
  email?: string;

  @ApiProperty({
    description: 'Quality bucket assignment',
    enum: BucketType,
    example: BucketType.GOOD,
  })
  bucket: BucketType;

  @ApiProperty({
    description: 'Speaker status',
    enum: SpeakerStatus,
    example: SpeakerStatus.ACTIVE,
  })
  status: SpeakerStatus;

  @ApiPropertyOptional({
    description: 'Additional notes about the speaker',
    example: 'Cardiologist with 15 years of experience',
  })
  notes?: string;

  @ApiProperty({
    description: 'Additional metadata',
    example: {
      specialty: 'Cardiology',
      hospital: 'General Hospital',
    },
  })
  metadata: Record<string, any>;

  @ApiProperty({
    description: 'Creation timestamp',
    example: '2024-01-15T10:30:00Z',
  })
  createdAt: Date;

  @ApiProperty({
    description: 'Last update timestamp',
    example: '2024-01-15T10:30:00Z',
  })
  updatedAt: Date;

  @ApiPropertyOptional({
    description: 'Deletion timestamp (if soft deleted)',
    example: '2024-01-15T10:30:00Z',
  })
  deletedAt?: Date;
}

export class PaginatedSpeakersResponseDto {
  @ApiProperty({
    description: 'List of speakers',
    type: [SpeakerResponseDto],
  })
  data: SpeakerResponseDto[];

  @ApiProperty({
    description: 'Pagination metadata',
    example: {
      page: 1,
      limit: 20,
      total: 100,
      totalPages: 5,
      hasNext: true,
      hasPrevious: false,
    },
  })
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
    hasNext: boolean;
    hasPrevious: boolean;
  };
}

