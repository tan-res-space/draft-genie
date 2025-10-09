import { Controller, Get, Param, UseGuards } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiResponse, ApiBearerAuth, ApiParam } from '@nestjs/swagger';
import { AggregationService } from './aggregation.service';
import { JwtAuthGuard } from '../auth/guards/jwt-auth.guard';

@ApiTags('aggregation')
@Controller()
@UseGuards(JwtAuthGuard)
@ApiBearerAuth('JWT')
export class AggregationController {
  constructor(private readonly aggregationService: AggregationService) {}

  @Get('speakers/:id/complete')
  @ApiOperation({ 
    summary: 'Get complete speaker data',
    description: 'Aggregates speaker data with all associated drafts, evaluations, and metrics from multiple services'
  })
  @ApiParam({ name: 'id', description: 'Speaker ID', example: '123e4567-e89b-12d3-a456-426614174000' })
  @ApiResponse({ 
    status: 200, 
    description: 'Complete speaker data retrieved successfully',
    schema: {
      type: 'object',
      properties: {
        speaker: { type: 'object', description: 'Speaker details from Speaker Service' },
        drafts: { 
          type: 'object',
          properties: {
            data: { type: 'array', description: 'List of drafts' },
            error: { type: 'string', nullable: true }
          }
        },
        evaluations: { 
          type: 'object',
          properties: {
            data: { type: 'array', description: 'List of evaluations' },
            error: { type: 'string', nullable: true }
          }
        },
        metrics: { 
          type: 'object',
          properties: {
            data: { type: 'object', description: 'Aggregated metrics' },
            error: { type: 'string', nullable: true }
          }
        },
        summary: {
          type: 'object',
          properties: {
            totalDrafts: { type: 'number' },
            totalEvaluations: { type: 'number' },
            hasMetrics: { type: 'boolean' }
          }
        },
        aggregatedAt: { type: 'string', format: 'date-time' }
      }
    }
  })
  @ApiResponse({ status: 404, description: 'Speaker not found' })
  @ApiResponse({ status: 401, description: 'Unauthorized' })
  async getSpeakerComplete(@Param('id') id: string) {
    return this.aggregationService.getSpeakerComplete(id);
  }

  @Get('dashboard/metrics')
  @ApiOperation({ 
    summary: 'Get dashboard metrics',
    description: 'Aggregates metrics from all services for dashboard display'
  })
  @ApiResponse({ 
    status: 200, 
    description: 'Dashboard metrics retrieved successfully',
    schema: {
      type: 'object',
      properties: {
        speakers: {
          type: 'object',
          properties: {
            data: { type: 'object', description: 'Speaker statistics' },
            error: { type: 'string', nullable: true }
          }
        },
        evaluations: {
          type: 'object',
          properties: {
            data: { type: 'object', description: 'Evaluation metrics' },
            error: { type: 'string', nullable: true }
          }
        },
        drafts: {
          type: 'object',
          properties: {
            data: { type: 'object', description: 'Draft statistics' },
            error: { type: 'string', nullable: true }
          }
        },
        summary: {
          type: 'object',
          properties: {
            totalSpeakers: { type: 'number' },
            totalDrafts: { type: 'number' },
            totalEvaluations: { type: 'number' },
            servicesHealthy: { type: 'number' },
            servicesTotal: { type: 'number' },
            healthPercentage: { type: 'number' }
          }
        },
        aggregatedAt: { type: 'string', format: 'date-time' }
      }
    }
  })
  @ApiResponse({ status: 401, description: 'Unauthorized' })
  async getDashboardMetrics() {
    return this.aggregationService.getDashboardMetrics();
  }
}

