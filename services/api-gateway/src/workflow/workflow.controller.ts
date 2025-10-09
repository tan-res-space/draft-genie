import { Controller, Post, Body, UseGuards } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiResponse, ApiBearerAuth } from '@nestjs/swagger';
import { WorkflowService } from './workflow.service';
import { GenerateDfnDto } from './dto/generate-dfn.dto';
import { JwtAuthGuard } from '../auth/guards/jwt-auth.guard';

@ApiTags('workflow')
@Controller('workflow')
@UseGuards(JwtAuthGuard)
@ApiBearerAuth('JWT')
export class WorkflowController {
  constructor(private readonly workflowService: WorkflowService) {}

  @Post('generate-dfn')
  @ApiOperation({ 
    summary: 'Generate DFN (Draft From Notes) - Complete Workflow',
    description: 'Orchestrates the complete DFN generation workflow across multiple services:\n' +
      '1. Validates speaker exists\n' +
      '2. Checks for existing drafts (IFN)\n' +
      '3. Triggers RAG service with LangGraph AI agent\n' +
      '4. Returns generated DFN with metadata\n\n' +
      'This endpoint coordinates Speaker, Draft, and RAG services to provide a seamless DFN generation experience.'
  })
  @ApiResponse({ 
    status: 201, 
    description: 'DFN generation workflow completed successfully',
    schema: {
      type: 'object',
      properties: {
        workflow: {
          type: 'object',
          properties: {
            status: { type: 'string', enum: ['completed', 'failed'] },
            steps: {
              type: 'array',
              items: {
                type: 'object',
                properties: {
                  step: { type: 'number' },
                  name: { type: 'string' },
                  status: { type: 'string' },
                  data: { type: 'object' }
                }
              }
            },
            completedAt: { type: 'string', format: 'date-time' }
          }
        },
        speaker: {
          type: 'object',
          properties: {
            id: { type: 'string' },
            name: { type: 'string' },
            bucket: { type: 'string' }
          }
        },
        generation: { type: 'object', description: 'RAG generation response' },
        dfn: { type: 'object', description: 'Generated DFN details' },
        metadata: {
          type: 'object',
          properties: {
            draftCount: { type: 'number' },
            prompt: { type: 'string' },
            usedLangGraph: { type: 'boolean' }
          }
        }
      }
    }
  })
  @ApiResponse({ status: 400, description: 'Bad request - Speaker has no drafts or invalid input' })
  @ApiResponse({ status: 401, description: 'Unauthorized' })
  @ApiResponse({ status: 404, description: 'Speaker not found' })
  async generateDfn(@Body() generateDfnDto: GenerateDfnDto) {
    return this.workflowService.generateDfn(generateDfnDto);
  }
}

