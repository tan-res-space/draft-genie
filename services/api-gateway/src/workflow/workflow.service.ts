import { Injectable, Logger, BadRequestException } from '@nestjs/common';
import { ProxyService, ServiceType } from '../proxy/proxy.service';
import { GenerateDfnDto } from './dto/generate-dfn.dto';

@Injectable()
export class WorkflowService {
  private readonly logger = new Logger(WorkflowService.name);

  constructor(private readonly proxyService: ProxyService) {}

  /**
   * Orchestrate complete DFN generation workflow
   * Steps:
   * 1. Validate speaker exists
   * 2. Check if speaker has drafts (IFN)
   * 3. Trigger RAG service to generate DFN
   * 4. Wait for generation to complete
   * 5. Return generated DFN with metadata
   */
  async generateDfn(generateDfnDto: GenerateDfnDto): Promise<any> {
    const { speakerId, prompt, context } = generateDfnDto;
    
    this.logger.log(`Starting DFN generation workflow for speaker ${speakerId}`);

    try {
      // Step 1: Validate speaker exists
      this.logger.debug('Step 1: Validating speaker');
      const speaker = await this.validateSpeaker(speakerId);

      // Step 2: Check if speaker has drafts
      this.logger.debug('Step 2: Checking for existing drafts');
      const drafts = await this.checkSpeakerDrafts(speakerId);

      if (!drafts || drafts.length === 0) {
        throw new BadRequestException(
          `Speaker ${speakerId} has no drafts. Please ingest drafts before generating DFN.`
        );
      }

      // Step 3: Trigger RAG service to generate DFN
      this.logger.debug('Step 3: Triggering RAG service for DFN generation');
      const ragRequest = {
        speaker_id: speakerId,
        prompt: prompt || 'Generate an improved draft based on the speaker\'s style and previous drafts',
        context: context || {},
        use_langgraph: true, // Use LangGraph AI agent
      };

      const dfnGeneration = await this.proxyService.post(
        ServiceType.RAG,
        '/api/v1/rag/generate',
        ragRequest
      );

      // Step 4: Get the generated DFN details
      this.logger.debug('Step 4: Retrieving generated DFN');
      let dfnDetails = null;
      if (dfnGeneration.dfn_id) {
        try {
          dfnDetails = await this.proxyService.get(
            ServiceType.RAG,
            `/api/v1/dfn/${dfnGeneration.dfn_id}`
          );
        } catch (error) {
          this.logger.warn(`Could not fetch DFN details: ${error.message}`);
        }
      }

      // Step 5: Build workflow response
      const result = {
        workflow: {
          status: 'completed',
          steps: [
            { step: 1, name: 'validate_speaker', status: 'completed', data: { speakerId: speaker.id, name: speaker.name } },
            { step: 2, name: 'check_drafts', status: 'completed', data: { draftCount: drafts.length } },
            { step: 3, name: 'generate_dfn', status: 'completed', data: dfnGeneration },
            { step: 4, name: 'retrieve_dfn', status: dfnDetails ? 'completed' : 'partial', data: dfnDetails },
          ],
          completedAt: new Date().toISOString(),
        },
        speaker: {
          id: speaker.id,
          name: speaker.name,
          bucket: speaker.bucket,
        },
        generation: dfnGeneration,
        dfn: dfnDetails,
        metadata: {
          draftCount: drafts.length,
          prompt: prompt || 'Default prompt',
          usedLangGraph: true,
        },
      };

      this.logger.log(`DFN generation workflow completed for speaker ${speakerId}`);
      return result;

    } catch (error) {
      this.logger.error(`DFN generation workflow failed: ${error.message}`);
      
      // Return detailed error response
      return {
        workflow: {
          status: 'failed',
          error: error.message,
          failedAt: new Date().toISOString(),
        },
        speaker: { id: speakerId },
      };
    }
  }

  /**
   * Validate that speaker exists
   */
  private async validateSpeaker(speakerId: string): Promise<any> {
    try {
      const speaker = await this.proxyService.get(
        ServiceType.SPEAKER,
        `/api/v1/speakers/${speakerId}`
      );
      return speaker;
    } catch (error) {
      throw new BadRequestException(`Speaker ${speakerId} not found`);
    }
  }

  /**
   * Check if speaker has drafts
   */
  private async checkSpeakerDrafts(speakerId: string): Promise<any[]> {
    try {
      const drafts = await this.proxyService.get(
        ServiceType.DRAFT,
        `/api/v1/drafts/speaker/${speakerId}`
      );
      return Array.isArray(drafts) ? drafts : [];
    } catch (error) {
      this.logger.warn(`Could not fetch drafts for speaker ${speakerId}: ${error.message}`);
      return [];
    }
  }
}

