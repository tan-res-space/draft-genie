import { ApiProperty } from '@nestjs/swagger';
import { EvaluationStatus } from '../../common/constants/enums';

export class EvaluationResponseDto {
  @ApiProperty({
    description: 'Evaluation ID',
    example: '123e4567-e89b-12d3-a456-426614174000',
  })
  id: string;

  @ApiProperty({
    description: 'Speaker ID',
    example: '123e4567-e89b-12d3-a456-426614174001',
  })
  speakerId: string;

  @ApiProperty({
    description: 'Draft ID',
    example: '123e4567-e89b-12d3-a456-426614174002',
  })
  draftId: string;

  @ApiProperty({
    description: 'Evaluation status',
    enum: EvaluationStatus,
    example: EvaluationStatus.COMPLETED,
  })
  status: EvaluationStatus;

  @ApiProperty({
    description: 'Evaluation metrics',
    example: { clarity: 8.5, engagement: 9.0, technical: 7.5 },
  })
  metrics: Record<string, any>;

  @ApiProperty({
    description: 'Evaluation results',
    example: { summary: 'Good presentation', strengths: ['Clear delivery'] },
  })
  results: Record<string, any>;

  @ApiProperty({
    description: 'Additional notes',
    example: 'Evaluated using automated system',
    nullable: true,
  })
  notes: string | null;

  @ApiProperty({
    description: 'Creation timestamp',
    example: '2024-01-01T00:00:00.000Z',
  })
  createdAt: Date;

  @ApiProperty({
    description: 'Last update timestamp',
    example: '2024-01-01T00:00:00.000Z',
  })
  updatedAt: Date;
}

export class PaginatedEvaluationsResponseDto {
  @ApiProperty({
    description: 'Array of evaluations',
    type: [EvaluationResponseDto],
  })
  data: EvaluationResponseDto[];

  @ApiProperty({
    description: 'Pagination metadata',
    example: {
      page: 1,
      limit: 10,
      total: 100,
      totalPages: 10,
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

