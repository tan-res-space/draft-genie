/**
 * Update Speaker DTO
 */

import { ApiPropertyOptional } from '@nestjs/swagger';
import {
  IsString,
  IsEmail,
  IsEnum,
  IsOptional,
  IsObject,
  MinLength,
  MaxLength,
} from 'class-validator';
import { SpeakerStatus } from '../../common/constants/enums';

export class UpdateSpeakerDto {
  @ApiPropertyOptional({
    description: 'Speaker name',
    example: 'Dr. John Smith',
    minLength: 2,
    maxLength: 255,
  })
  @IsOptional()
  @IsString()
  @MinLength(2)
  @MaxLength(255)
  name?: string;

  @ApiPropertyOptional({
    description: 'Speaker email address',
    example: 'john.smith@hospital.com',
  })
  @IsOptional()
  @IsEmail()
  @MaxLength(255)
  email?: string;

  @ApiPropertyOptional({
    description: 'Speaker status',
    enum: SpeakerStatus,
  })
  @IsOptional()
  @IsEnum(SpeakerStatus)
  status?: SpeakerStatus;

  @ApiPropertyOptional({
    description: 'Additional notes about the speaker',
    example: 'Cardiologist with 15 years of experience',
  })
  @IsOptional()
  @IsString()
  @MaxLength(2000)
  notes?: string;

  @ApiPropertyOptional({
    description: 'Additional metadata (JSON object)',
    example: {
      specialty: 'Cardiology',
      hospital: 'General Hospital',
      yearsOfExperience: 15,
    },
  })
  @IsOptional()
  @IsObject()
  metadata?: Record<string, any>;
}

