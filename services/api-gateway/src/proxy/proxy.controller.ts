import {
  Controller,
  All,
  Req,
  Res,
  UseGuards,
  Logger,
} from '@nestjs/common';
import { Request, Response } from 'express';
import { ApiTags, ApiBearerAuth, ApiExcludeEndpoint } from '@nestjs/swagger';
import { ProxyService, ServiceType } from './proxy.service';
import { JwtAuthGuard } from '../auth/guards/jwt-auth.guard';

@ApiTags('proxy')
@Controller()
@UseGuards(JwtAuthGuard)
@ApiBearerAuth('JWT')
export class ProxyController {
  private readonly logger = new Logger(ProxyController.name);

  constructor(private readonly proxyService: ProxyService) {}

  @All('speakers*')
  @ApiExcludeEndpoint()
  async proxySpeakers(@Req() req: Request, @Res() res: Response) {
    return this.proxyToService(ServiceType.SPEAKER, req, res);
  }

  @All('drafts*')
  @ApiExcludeEndpoint()
  async proxyDrafts(@Req() req: Request, @Res() res: Response) {
    return this.proxyToService(ServiceType.DRAFT, req, res);
  }

  @All('rag*')
  @ApiExcludeEndpoint()
  async proxyRag(@Req() req: Request, @Res() res: Response) {
    return this.proxyToService(ServiceType.RAG, req, res);
  }

  @All('evaluations*')
  @ApiExcludeEndpoint()
  async proxyEvaluations(@Req() req: Request, @Res() res: Response) {
    return this.proxyToService(ServiceType.EVALUATION, req, res);
  }

  @All('metrics*')
  @ApiExcludeEndpoint()
  async proxyMetrics(@Req() req: Request, @Res() res: Response) {
    return this.proxyToService(ServiceType.EVALUATION, req, res);
  }

  private async proxyToService(
    service: ServiceType,
    req: Request,
    res: Response,
  ) {
    try {
      const path = req.url;
      const method = req.method;
      const data = method === 'GET' ? req.query : req.body;
      
      // Forward authorization header if present
      const headers: Record<string, string> = {};
      if (req.headers.authorization) {
        headers['authorization'] = req.headers.authorization;
      }

      this.logger.debug(`Proxying ${method} ${path} to ${service} service`);

      const result = await this.proxyService.proxyRequest(
        service,
        path,
        method,
        data,
        headers,
      );

      return res.json(result);
    } catch (error) {
      this.logger.error(`Proxy error: ${error.message}`);
      throw error;
    }
  }
}
