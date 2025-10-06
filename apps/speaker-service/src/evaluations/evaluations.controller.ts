import {
  Controller,
  Get,
  Post,
  Body,
  Patch,
  Param,
  Delete,
  Query,
  HttpCode,
  HttpStatus,
  Logger,
} from '@nestjs/common';
import { ApiTags, ApiOperation, ApiResponse, ApiParam } from '@nestjs/swagger';
import { EvaluationsService } from './evaluations.service';
import { CreateEvaluationDto } from './dto/create-evaluation.dto';
import { UpdateEvaluationDto } from './dto/update-evaluation.dto';
import { QueryEvaluationsDto } from './dto/query-evaluations.dto';
import {
  EvaluationResponseDto,
  PaginatedEvaluationsResponseDto,
} from './dto/evaluation-response.dto';

@ApiTags('evaluations')
@Controller('api/v1/evaluations')
export class EvaluationsController {
  private readonly logger = new Logger(EvaluationsController.name);

  constructor(private readonly evaluationsService: EvaluationsService) {}

  @Post()
  @ApiOperation({
    summary: 'Create a new evaluation',
    description: 'Create a new evaluation for a speaker and draft',
  })
  @ApiResponse({
    status: 201,
    description: 'Evaluation created successfully',
    type: EvaluationResponseDto,
  })
  @ApiResponse({
    status: 400,
    description: 'Invalid input data',
  })
  @ApiResponse({
    status: 404,
    description: 'Speaker not found',
  })
  async create(@Body() createEvaluationDto: CreateEvaluationDto): Promise<EvaluationResponseDto> {
    this.logger.log(`POST /evaluations - Creating evaluation for speaker ${createEvaluationDto.speakerId}`);
    return await this.evaluationsService.create(createEvaluationDto) as any;
  }

  @Get()
  @ApiOperation({
    summary: 'Get all evaluations',
    description: 'Retrieve a paginated list of evaluations with optional filters',
  })
  @ApiResponse({
    status: 200,
    description: 'Evaluations retrieved successfully',
    type: PaginatedEvaluationsResponseDto,
  })
  async findAll(@Query() query: QueryEvaluationsDto): Promise<PaginatedEvaluationsResponseDto> {
    this.logger.log(`GET /evaluations - Query: ${JSON.stringify(query)}`);
    return await this.evaluationsService.findAll(query);
  }

  @Get('statistics')
  @ApiOperation({
    summary: 'Get evaluation statistics',
    description: 'Get aggregate statistics for evaluations',
  })
  @ApiResponse({
    status: 200,
    description: 'Statistics retrieved successfully',
  })
  async getStatistics() {
    this.logger.log('GET /evaluations/statistics');
    return await this.evaluationsService.getStatistics();
  }

  @Get(':id')
  @ApiOperation({
    summary: 'Get evaluation by ID',
    description: 'Retrieve a single evaluation by its ID',
  })
  @ApiParam({
    name: 'id',
    description: 'Evaluation ID',
    example: '123e4567-e89b-12d3-a456-426614174000',
  })
  @ApiResponse({
    status: 200,
    description: 'Evaluation retrieved successfully',
    type: EvaluationResponseDto,
  })
  @ApiResponse({
    status: 404,
    description: 'Evaluation not found',
  })
  async findOne(@Param('id') id: string): Promise<EvaluationResponseDto> {
    this.logger.log(`GET /evaluations/${id}`);
    return await this.evaluationsService.findOne(id) as any;
  }

  @Patch(':id')
  @ApiOperation({
    summary: 'Update evaluation',
    description: 'Update evaluation status, metrics, results, or notes',
  })
  @ApiParam({
    name: 'id',
    description: 'Evaluation ID',
    example: '123e4567-e89b-12d3-a456-426614174000',
  })
  @ApiResponse({
    status: 200,
    description: 'Evaluation updated successfully',
    type: EvaluationResponseDto,
  })
  @ApiResponse({
    status: 400,
    description: 'Invalid input data',
  })
  @ApiResponse({
    status: 404,
    description: 'Evaluation not found',
  })
  async update(
    @Param('id') id: string,
    @Body() updateEvaluationDto: UpdateEvaluationDto,
  ): Promise<EvaluationResponseDto> {
    this.logger.log(`PATCH /evaluations/${id}`);
    return await this.evaluationsService.update(id, updateEvaluationDto) as any;
  }

  @Delete(':id')
  @HttpCode(HttpStatus.NO_CONTENT)
  @ApiOperation({
    summary: 'Delete evaluation',
    description: 'Soft delete an evaluation',
  })
  @ApiParam({
    name: 'id',
    description: 'Evaluation ID',
    example: '123e4567-e89b-12d3-a456-426614174000',
  })
  @ApiResponse({
    status: 204,
    description: 'Evaluation deleted successfully',
  })
  @ApiResponse({
    status: 404,
    description: 'Evaluation not found',
  })
  async remove(@Param('id') id: string): Promise<void> {
    this.logger.log(`DELETE /evaluations/${id}`);
    await this.evaluationsService.remove(id);
  }
}

