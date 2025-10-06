/**
 * Query Speakers DTO
 */

import { ApiPropertyOptional } from '@nestjs/swagger';
import { IsEnum, IsOptional, IsString, IsInt, Min, Max } from 'class-validator';
import { Type } from 'class-transformer';
import { BucketType, SpeakerStatus } from '../../common/constants/enums';
import { DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE } from '../../common/constants/enums';

export class QuerySpeakersDto {
  @ApiPropertyOptional({
    description: 'Page number (1-based)',
    example: 1,
    default: 1,
    minimum: 1,
  })
  @IsOptional()
  @Type(() => Number)
  @IsInt()
  @Min(1)
  page?: number = 1;

  @ApiPropertyOptional({
    description: 'Number of items per page',
    example: 20,
    default: DEFAULT_PAGE_SIZE,
    minimum: 1,
    maximum: MAX_PAGE_SIZE,
  })
  @IsOptional()
  @Type(() => Number)
  @IsInt()
  @Min(1)
  @Max(MAX_PAGE_SIZE)
  limit?: number = DEFAULT_PAGE_SIZE;

  @ApiPropertyOptional({
    description: 'Field to sort by',
    example: 'createdAt',
    default: 'createdAt',
  })
  @IsOptional()
  @IsString()
  sortBy?: string = 'createdAt';

  @ApiPropertyOptional({
    description: 'Sort order',
    enum: ['asc', 'desc'],
    example: 'desc',
    default: 'desc',
  })
  @IsOptional()
  @IsEnum(['asc', 'desc'])
  sortOrder?: 'asc' | 'desc' = 'desc';

  @ApiPropertyOptional({
    description: 'Filter by bucket type',
    enum: BucketType,
    example: BucketType.GOOD,
  })
  @IsOptional()
  @IsEnum(BucketType)
  bucket?: BucketType;

  @ApiPropertyOptional({
    description: 'Filter by status',
    enum: SpeakerStatus,
    example: SpeakerStatus.ACTIVE,
  })
  @IsOptional()
  @IsEnum(SpeakerStatus)
  status?: SpeakerStatus;

  @ApiPropertyOptional({
    description: 'Search by name, email, or external ID',
    example: 'John',
  })
  @IsOptional()
  @IsString()
  search?: string;
}

