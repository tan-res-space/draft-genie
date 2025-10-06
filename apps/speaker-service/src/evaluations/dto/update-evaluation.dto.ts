import { ApiProperty } from '@nestjs/swagger';
import { IsString, IsOptional, IsObject, IsEnum } from 'class-validator';
import { EvaluationStatus } from '../../common/constants/enums';

export class UpdateEvaluationDto {
  @ApiProperty({
    description: 'Evaluation status',
    enum: EvaluationStatus,
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
    example: 'Updated after review',
    required: false,
  })
  @IsOptional()
  @IsString()
  notes?: string;
}

