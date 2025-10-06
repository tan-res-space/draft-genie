import { ApiProperty } from '@nestjs/swagger';
import { IsString, IsUUID, IsOptional, IsObject, IsEnum } from 'class-validator';
import { EvaluationStatus } from '../../common/constants/enums';

export class CreateEvaluationDto {
  @ApiProperty({
    description: 'Speaker ID to evaluate',
    example: '123e4567-e89b-12d3-a456-426614174000',
  })
  @IsUUID()
  speakerId: string;

  @ApiProperty({
    description: 'Draft ID associated with this evaluation',
    example: '123e4567-e89b-12d3-a456-426614174001',
  })
  @IsUUID()
  draftId: string;

  @ApiProperty({
    description: 'Evaluation status',
    enum: EvaluationStatus,
    default: EvaluationStatus.PENDING,
    required: false,
  })
  @IsOptional()
  @IsEnum(EvaluationStatus)
  status?: EvaluationStatus;

  @ApiProperty({
    description: 'Evaluation metrics (scores, ratings, etc.)',
    example: { clarity: 8.5, engagement: 9.0, technical: 7.5 },
    required: false,
  })
  @IsOptional()
  @IsObject()
  metrics?: Record<string, any>;

  @ApiProperty({
    description: 'Evaluation results and feedback',
    example: { summary: 'Good presentation', strengths: ['Clear delivery'], improvements: ['More examples'] },
    required: false,
  })
  @IsOptional()
  @IsObject()
  results?: Record<string, any>;

  @ApiProperty({
    description: 'Additional notes',
    example: 'Evaluated using automated system',
    required: false,
  })
  @IsOptional()
  @IsString()
  notes?: string;
}

