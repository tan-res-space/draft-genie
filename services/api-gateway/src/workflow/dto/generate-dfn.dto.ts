import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';
import { IsString, IsOptional, IsObject } from 'class-validator';

export class GenerateDfnDto {
  @ApiProperty({
    description: 'Speaker ID for whom to generate the DFN',
    example: '123e4567-e89b-12d3-a456-426614174000',
  })
  @IsString()
  speakerId: string;

  @ApiPropertyOptional({
    description: 'Custom prompt for DFN generation',
    example: 'Generate an improved draft focusing on clarity and conciseness',
  })
  @IsString()
  @IsOptional()
  prompt?: string;

  @ApiPropertyOptional({
    description: 'Additional context for generation',
    example: { topic: 'technical documentation', tone: 'professional' },
  })
  @IsObject()
  @IsOptional()
  context?: Record<string, any>;
}

