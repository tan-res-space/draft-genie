#!/bin/bash

###############################################################################
# PostgreSQL to SQL Server Migration Script
# 
# This script automates the migration of the Speaker Service database
# from PostgreSQL to Microsoft SQL Server.
#
# Usage: ./scripts/migrate-to-sqlserver.sh [--dry-run] [--backup] [--rollback]
#
# Options:
#   --dry-run   : Show what would be changed without making changes
#   --backup    : Create backup of PostgreSQL data before migration
#   --rollback  : Rollback to PostgreSQL (requires backup)
#   --help      : Show this help message
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKUP_DIR="$PROJECT_ROOT/backups/postgres-$(date +%Y%m%d-%H%M%S)"
DRY_RUN=false
BACKUP=false
ROLLBACK=false

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --backup)
      BACKUP=true
      shift
      ;;
    --rollback)
      ROLLBACK=true
      shift
      ;;
    --help)
      head -n 15 "$0" | tail -n 13
      exit 0
      ;;
    *)
      echo -e "${RED}Unknown option: $1${NC}"
      echo "Use --help for usage information"
      exit 1
      ;;
  esac
done

###############################################################################
# Helper Functions
###############################################################################

log_info() {
  echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
  echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
  echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
  echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
  log_info "Checking prerequisites..."
  
  # Check Docker
  if ! command -v docker &> /dev/null; then
    log_error "Docker is not installed"
    exit 1
  fi
  
  # Check Docker Compose
  if ! command -v docker-compose &> /dev/null; then
    log_error "Docker Compose is not installed"
    exit 1
  fi
  
  # Check Node.js
  if ! command -v node &> /dev/null; then
    log_error "Node.js is not installed"
    exit 1
  fi
  
  # Check npx
  if ! command -v npx &> /dev/null; then
    log_error "npx is not installed"
    exit 1
  fi
  
  log_success "All prerequisites met"
}

backup_postgres() {
  log_info "Creating PostgreSQL backup..."
  
  mkdir -p "$BACKUP_DIR"
  
  # Backup database
  docker exec draft-genie-postgres pg_dump -U draftgenie draftgenie > "$BACKUP_DIR/draftgenie.sql"
  
  # Backup configuration files
  cp "$PROJECT_ROOT/apps/speaker-service/prisma/schema.prisma" "$BACKUP_DIR/schema.prisma.bak"
  cp "$PROJECT_ROOT/docker/.env" "$BACKUP_DIR/.env.bak"
  cp "$PROJECT_ROOT/docker/docker-compose.yml" "$BACKUP_DIR/docker-compose.yml.bak"
  
  log_success "Backup created at: $BACKUP_DIR"
}

update_prisma_schema() {
  log_info "Updating Prisma schema..."
  
  local schema_file="$PROJECT_ROOT/apps/speaker-service/prisma/schema.prisma"
  
  if [ "$DRY_RUN" = true ]; then
    log_warning "DRY RUN: Would update $schema_file"
    return
  fi
  
  # Update provider
  sed -i.bak 's/provider = "postgresql"/provider = "sqlserver"/' "$schema_file"
  
  log_success "Prisma schema updated"
}

update_env_files() {
  log_info "Updating environment files..."
  
  if [ "$DRY_RUN" = true ]; then
    log_warning "DRY RUN: Would update environment files"
    return
  fi
  
  # Update docker/.env
  cat >> "$PROJECT_ROOT/docker/.env" << 'EOF'

# SQL Server Configuration (added by migration script)
SQLSERVER_SA_PASSWORD=DraftGenie123!
SQLSERVER_DB=draftgenie
SQLSERVER_PORT=1433
EOF
  
  # Update .env.example
  local env_example="$PROJECT_ROOT/apps/speaker-service/.env.example"
  sed -i.bak 's|DATABASE_URL=postgresql://.*|DATABASE_URL=sqlserver://localhost:1433;database=draftgenie;user=sa;password=DraftGenie123!;encrypt=true;trustServerCertificate=true|' "$env_example"
  
  log_success "Environment files updated"
}

update_docker_compose() {
  log_info "Updating Docker Compose configuration..."
  
  if [ "$DRY_RUN" = true ]; then
    log_warning "DRY RUN: Would update docker-compose.yml"
    return
  fi
  
  # This is a simplified version - in production, use a proper YAML parser
  log_warning "Docker Compose update requires manual intervention"
  log_info "Please update docker/docker-compose.yml manually following the migration guide"
  log_info "See: docs/POSTGRESQL_TO_SQLSERVER_MIGRATION_ANALYSIS.md"
}

stop_services() {
  log_info "Stopping services..."
  
  if [ "$DRY_RUN" = true ]; then
    log_warning "DRY RUN: Would stop services"
    return
  fi
  
  cd "$PROJECT_ROOT"
  docker-compose -f docker/docker-compose.yml down
  
  log_success "Services stopped"
}

start_sqlserver() {
  log_info "Starting SQL Server..."
  
  if [ "$DRY_RUN" = true ]; then
    log_warning "DRY RUN: Would start SQL Server"
    return
  fi
  
  cd "$PROJECT_ROOT"
  docker-compose -f docker/docker-compose.yml up -d sqlserver
  
  # Wait for SQL Server to be ready
  log_info "Waiting for SQL Server to be ready..."
  sleep 30
  
  log_success "SQL Server started"
}

run_prisma_migration() {
  log_info "Running Prisma migration..."
  
  if [ "$DRY_RUN" = true ]; then
    log_warning "DRY RUN: Would run Prisma migration"
    return
  fi
  
  cd "$PROJECT_ROOT"
  
  # Generate Prisma client
  npx prisma generate --schema=apps/speaker-service/prisma/schema.prisma
  
  # Run migration
  npx prisma migrate dev --name init_sqlserver --schema=apps/speaker-service/prisma/schema.prisma
  
  log_success "Prisma migration completed"
}

start_all_services() {
  log_info "Starting all services..."
  
  if [ "$DRY_RUN" = true ]; then
    log_warning "DRY RUN: Would start all services"
    return
  fi
  
  cd "$PROJECT_ROOT"
  docker-compose -f docker/docker-compose.yml up -d
  
  log_success "All services started"
}

verify_migration() {
  log_info "Verifying migration..."
  
  if [ "$DRY_RUN" = true ]; then
    log_warning "DRY RUN: Would verify migration"
    return
  fi
  
  # Wait for services to be ready
  sleep 10
  
  # Check health endpoint
  if curl -f http://localhost:3001/api/v1/health > /dev/null 2>&1; then
    log_success "Health check passed"
  else
    log_error "Health check failed"
    exit 1
  fi
  
  # Run tests
  log_info "Running tests..."
  cd "$PROJECT_ROOT"
  npm run test -- apps/speaker-service
  
  log_success "Migration verified successfully"
}

rollback_migration() {
  log_info "Rolling back to PostgreSQL..."
  
  if [ ! -d "$BACKUP_DIR" ]; then
    log_error "No backup found. Cannot rollback."
    exit 1
  fi
  
  # Stop services
  stop_services
  
  # Restore configuration files
  cp "$BACKUP_DIR/schema.prisma.bak" "$PROJECT_ROOT/apps/speaker-service/prisma/schema.prisma"
  cp "$BACKUP_DIR/.env.bak" "$PROJECT_ROOT/docker/.env"
  cp "$BACKUP_DIR/docker-compose.yml.bak" "$PROJECT_ROOT/docker/docker-compose.yml"
  
  # Regenerate Prisma client
  cd "$PROJECT_ROOT"
  npx prisma generate --schema=apps/speaker-service/prisma/schema.prisma
  
  # Start PostgreSQL
  docker-compose -f docker/docker-compose.yml up -d postgres
  sleep 10
  
  # Restore database
  docker exec -i draft-genie-postgres psql -U draftgenie draftgenie < "$BACKUP_DIR/draftgenie.sql"
  
  # Start all services
  start_all_services
  
  log_success "Rollback completed"
}

###############################################################################
# Main Migration Flow
###############################################################################

main() {
  echo ""
  echo "╔════════════════════════════════════════════════════════════════╗"
  echo "║   PostgreSQL to SQL Server Migration Script                   ║"
  echo "║   Speaker Service Database Migration                          ║"
  echo "╚════════════════════════════════════════════════════════════════╝"
  echo ""
  
  if [ "$ROLLBACK" = true ]; then
    rollback_migration
    exit 0
  fi
  
  check_prerequisites
  
  if [ "$BACKUP" = true ]; then
    backup_postgres
  fi
  
  if [ "$DRY_RUN" = true ]; then
    log_warning "DRY RUN MODE - No changes will be made"
    echo ""
  fi
  
  # Migration steps
  update_prisma_schema
  update_env_files
  update_docker_compose
  
  if [ "$DRY_RUN" = false ]; then
    stop_services
    start_sqlserver
    run_prisma_migration
    start_all_services
    verify_migration
    
    echo ""
    log_success "Migration completed successfully!"
    echo ""
    log_info "Next steps:"
    echo "  1. Review the migration logs"
    echo "  2. Test all API endpoints manually"
    echo "  3. Monitor application logs for errors"
    echo "  4. Update documentation if needed"
    echo ""
    
    if [ "$BACKUP" = true ]; then
      log_info "Backup location: $BACKUP_DIR"
      log_info "To rollback: ./scripts/migrate-to-sqlserver.sh --rollback"
    fi
  else
    echo ""
    log_info "Dry run completed. Review the changes above."
    log_info "To perform the actual migration, run without --dry-run flag"
  fi
  
  echo ""
}

# Run main function
main

