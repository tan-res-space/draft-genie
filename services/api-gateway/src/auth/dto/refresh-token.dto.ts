import { ApiProperty } from '@nestjs/swagger';
import { IsString } from 'class-validator';

export class RefreshTokenDto {
  @ApiProperty({
    description: 'Refresh token received during login',
    example: '550e8400-e29b-41d4-a716-446655440000',
  })
  @IsString()
  refreshToken: string;
}

