/**
 * Update Bucket DTO
 */

import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';
import { IsEnum, IsOptional, IsString, MaxLength } from 'class-validator';
import { BucketType } from '../../common/constants/enums';

export class UpdateBucketDto {
  @ApiProperty({
    description: 'New quality bucket assignment',
    enum: BucketType,
    example: BucketType.EXCELLENT,
  })
  @IsEnum(BucketType)
  bucket: BucketType;

  @ApiPropertyOptional({
    description: 'Reason for bucket reassignment',
    example: 'Improved quality metrics after recent evaluations',
  })
  @IsOptional()
  @IsString()
  @MaxLength(500)
  reason?: string;
}

