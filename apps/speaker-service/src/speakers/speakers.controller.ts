/**
 * Speakers Controller - REST API endpoints for speaker management
 */

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
  Put,
} from '@nestjs/common';
import {
  ApiTags,
  ApiOperation,
  ApiResponse,
  ApiParam,
  ApiBearerAuth,
} from '@nestjs/swagger';
import { SpeakersService } from './speakers.service';
import { EvaluationsService } from '../evaluations/evaluations.service';
import { CreateSpeakerDto } from './dto/create-speaker.dto';
import { UpdateSpeakerDto } from './dto/update-speaker.dto';
import { UpdateBucketDto } from './dto/update-bucket.dto';
import { QuerySpeakersDto } from './dto/query-speakers.dto';
import {
  SpeakerResponseDto,
  PaginatedSpeakersResponseDto,
} from './dto/speaker-response.dto';
import { EvaluationResponseDto } from '../evaluations/dto/evaluation-response.dto';

@ApiTags('speakers')
@Controller('speakers')
@ApiBearerAuth()
export class SpeakersController {
  private readonly logger = new Logger(SpeakersController.name);

  constructor(
    private readonly speakersService: SpeakersService,
    private readonly evaluationsService: EvaluationsService,
  ) {}

  @Post()
  @ApiOperation({
    summary: 'Create a new speaker (SSA - Speaker Self-Addition)',
    description: 'Creates a new speaker in the system with initial bucket assignment',
  })
  @ApiResponse({
    status: 201,
    description: 'Speaker created successfully',
    type: SpeakerResponseDto,
  })
  @ApiResponse({
    status: 400,
    description: 'Invalid input data',
  })
  @ApiResponse({
    status: 409,
    description: 'Speaker with external ID already exists',
  })
  async create(@Body() createSpeakerDto: CreateSpeakerDto): Promise<SpeakerResponseDto> {
    this.logger.log(`POST /speakers - Creating speaker: ${createSpeakerDto.name}`);
    return await this.speakersService.create(createSpeakerDto) as any;
  }

  @Get()
  @ApiOperation({
    summary: 'Get all speakers',
    description: 'Retrieve a paginated list of speakers with optional filters',
  })
  @ApiResponse({
    status: 200,
    description: 'Speakers retrieved successfully',
    type: PaginatedSpeakersResponseDto,
  })
  async findAll(
    @Query() query: QuerySpeakersDto,
  ): Promise<PaginatedSpeakersResponseDto> {
    this.logger.log(`GET /speakers - Query: ${JSON.stringify(query)}`);
    return await this.speakersService.findAll(query);
  }

  @Get('statistics')
  @ApiOperation({
    summary: 'Get speaker statistics',
    description: 'Retrieve aggregate statistics about speakers',
  })
  @ApiResponse({
    status: 200,
    description: 'Statistics retrieved successfully',
  })
  async getStatistics() {
    this.logger.log('GET /speakers/statistics');
    return await this.speakersService.getStatistics();
  }

  @Get(':id')
  @ApiOperation({
    summary: 'Get speaker by ID',
    description: 'Retrieve detailed information about a specific speaker',
  })
  @ApiParam({
    name: 'id',
    description: 'Speaker ID',
    example: '550e8400-e29b-41d4-a716-446655440000',
  })
  @ApiResponse({
    status: 200,
    description: 'Speaker retrieved successfully',
    type: SpeakerResponseDto,
  })
  @ApiResponse({
    status: 404,
    description: 'Speaker not found',
  })
  async findOne(@Param('id') id: string): Promise<SpeakerResponseDto> {
    this.logger.log(`GET /speakers/${id}`);
    return await this.speakersService.findOne(id) as any;
  }

  @Patch(':id')
  @ApiOperation({
    summary: 'Update speaker',
    description: 'Update speaker information (name, email, status, notes, metadata)',
  })
  @ApiParam({
    name: 'id',
    description: 'Speaker ID',
    example: '550e8400-e29b-41d4-a716-446655440000',
  })
  @ApiResponse({
    status: 200,
    description: 'Speaker updated successfully',
    type: SpeakerResponseDto,
  })
  @ApiResponse({
    status: 404,
    description: 'Speaker not found',
  })
  async update(
    @Param('id') id: string,
    @Body() updateSpeakerDto: UpdateSpeakerDto,
  ): Promise<SpeakerResponseDto> {
    this.logger.log(`PATCH /speakers/${id}`);
    return await this.speakersService.update(id, updateSpeakerDto) as any;
  }

  @Put(':id/bucket')
  @ApiOperation({
    summary: 'Update speaker bucket',
    description: 'Reassign speaker to a different quality bucket',
  })
  @ApiParam({
    name: 'id',
    description: 'Speaker ID',
    example: '550e8400-e29b-41d4-a716-446655440000',
  })
  @ApiResponse({
    status: 200,
    description: 'Bucket updated successfully',
    type: SpeakerResponseDto,
  })
  @ApiResponse({
    status: 400,
    description: 'Speaker is already in the specified bucket',
  })
  @ApiResponse({
    status: 404,
    description: 'Speaker not found',
  })
  async updateBucket(
    @Param('id') id: string,
    @Body() updateBucketDto: UpdateBucketDto,
  ): Promise<SpeakerResponseDto> {
    this.logger.log(`PUT /speakers/${id}/bucket - New bucket: ${updateBucketDto.bucket}`);
    return await this.speakersService.updateBucket(id, updateBucketDto) as any;
  }

  @Delete(':id')
  @HttpCode(HttpStatus.NO_CONTENT)
  @ApiOperation({
    summary: 'Delete speaker',
    description: 'Soft delete a speaker (marks as deleted but retains data)',
  })
  @ApiParam({
    name: 'id',
    description: 'Speaker ID',
    example: '550e8400-e29b-41d4-a716-446655440000',
  })
  @ApiResponse({
    status: 204,
    description: 'Speaker deleted successfully',
  })
  @ApiResponse({
    status: 404,
    description: 'Speaker not found',
  })
  async remove(@Param('id') id: string): Promise<void> {
    this.logger.log(`DELETE /speakers/${id}`);
    await this.speakersService.remove(id);
  }

  @Get(':id/evaluations')
  @ApiOperation({
    summary: 'Get speaker evaluations',
    description: 'Retrieve all evaluations for a specific speaker',
  })
  @ApiParam({
    name: 'id',
    description: 'Speaker ID',
    example: '550e8400-e29b-41d4-a716-446655440000',
  })
  @ApiResponse({
    status: 200,
    description: 'Evaluations retrieved successfully',
    type: [EvaluationResponseDto],
  })
  @ApiResponse({
    status: 404,
    description: 'Speaker not found',
  })
  async getSpeakerEvaluations(@Param('id') id: string): Promise<EvaluationResponseDto[]> {
    this.logger.log(`GET /speakers/${id}/evaluations`);
    return await this.evaluationsService.findBySpeakerId(id) as any;
  }
}

