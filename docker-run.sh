#!/bin/bash
#
# GenEWeb Docker Management Script
# Facilite le lancement et la gestion des conteneurs Docker
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check dependencies
check_dependencies() {
    if ! command -v docker >/dev/null 2>&1; then
        log_error "Docker n'est pas installé. Veuillez installer Docker et réessayer."
        exit 1
    fi

    if ! command -v docker-compose >/dev/null 2>&1 && ! docker compose version >/dev/null 2>&1; then
        log_error "Docker Compose n'est pas disponible. Veuillez installer Docker Compose et réessayer."
        exit 1
    fi
}

# Function to show help
show_help() {
    cat << EOF
🚀 GenEWeb Docker Management Script

USAGE:
    $0 [COMMAND] [OPTIONS]

COMMANDS:
    build           Construire l'image Docker
    start           Démarrer GenEWeb (API seulement)
    dev             Démarrer en mode développement (API + Frontend dev)
    fullstack       Démarrer avec tmux (équivalent make run-fullstack-tmux)
    admin           Démarrer avec admin panel legacy
    stop            Arrêter tous les services
    restart         Redémarrer tous les services
    logs            Afficher les logs
    shell           Ouvrir un shell dans le conteneur
    clean           Nettoyer les images et volumes
    status          Afficher le statut des conteneurs
    help            Afficher cette aide

OPTIONS:
    --build         Forcer la reconstruction de l'image
    --follow        Suivre les logs en temps réel

EXAMPLES:
    $0 build                    # Construire l'image
    $0 start                    # Démarrer API seulement
    $0 dev                      # Mode développement complet
    $0 fullstack                # Fullstack avec tmux
    $0 logs --follow            # Suivre les logs
    $0 shell                    # Shell dans le conteneur
    $0 clean                    # Nettoyer tout

URLs:
    API Documentation:   http://localhost:8000/api/docs
    Frontend (dev):      http://localhost:5173
    Admin Panel:         http://localhost:2316
    Fullstack API:       http://localhost:8001
    Fullstack Frontend:  http://localhost:5174
EOF
}

# Build Docker image
build_image() {
    log_info "Construction de l'image Docker GenEWeb..."
    docker build -t geneweb-python:latest .
    log_success "Image construite avec succès!"
}

# Start services
start_service() {
    local profile="$1"
    local build_flag="$2"

    if [[ "$build_flag" == "--build" ]]; then
        log_info "Reconstruction de l'image demandée..."
        build_image
    fi

    case "$profile" in
        "")
            log_info "Démarrage de GenEWeb (API seulement)..."
            docker-compose up -d geneweb-app
            ;;
        "dev")
            log_info "Démarrage en mode développement (API + Frontend dev)..."
            docker-compose --profile dev up -d
            ;;
        "admin")
            log_info "Démarrage avec admin panel..."
            docker-compose --profile admin up -d
            ;;
        "fullstack")
            log_info "Démarrage fullstack avec tmux..."
            docker-compose --profile fullstack up -d
            ;;
        *)
            log_error "Profil inconnu: $profile"
            exit 1
            ;;
    esac

    log_success "Services démarrés!"
    show_urls "$profile"
}

# Show service URLs
show_urls() {
    local profile="$1"
    echo
    log_info "🌐 URLs disponibles:"

    case "$profile" in
        "")
            echo "  • API Documentation: http://localhost:8000/api/docs"
            echo "  • API ReDoc:         http://localhost:8000/api/redoc"
            ;;
        "dev")
            echo "  • API Documentation: http://localhost:8000/api/docs"
            echo "  • Frontend (dev):    http://localhost:5173"
            ;;
        "admin")
            echo "  • API Documentation: http://localhost:8000/api/docs"
            echo "  • Admin Panel:       http://localhost:2316"
            ;;
        "fullstack")
            echo "  • API Documentation: http://localhost:8001/api/docs"
            echo "  • Frontend (dev):    http://localhost:5174"
            echo "  • Admin Panel:       http://localhost:2317"
            ;;
    esac
    echo
}

# Stop services
stop_services() {
    log_info "Arrêt de tous les services GenEWeb..."
    docker-compose --profile dev --profile admin --profile fullstack down
    log_success "Tous les services arrêtés!"
}

# Restart services
restart_services() {
    stop_services
    start_service "$1" "$2"
}

# Show logs
show_logs() {
    local follow_flag="$1"

    if [[ "$follow_flag" == "--follow" ]]; then
        log_info "Affichage des logs en temps réel (Ctrl+C pour arrêter)..."
        docker-compose logs -f
    else
        log_info "Affichage des logs récents..."
        docker-compose logs --tail=50
    fi
}

# Open shell in container
open_shell() {
    local container_name="geneweb-app"

    if docker ps --format "table {{.Names}}" | grep -q "$container_name"; then
        log_info "Ouverture du shell dans le conteneur $container_name..."
        docker exec -it "$container_name" /bin/bash
    else
        log_error "Le conteneur $container_name n'est pas en cours d'exécution."
        log_info "Démarrez d'abord les services avec: $0 start"
        exit 1
    fi
}

# Clean Docker resources
clean_resources() {
    log_warning "⚠️  Cette action va supprimer les images, conteneurs et volumes GenEWeb."
    read -p "Êtes-vous sûr? (y/N): " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "Nettoyage des ressources Docker..."

        # Stop services
        docker-compose --profile dev --profile admin --profile fullstack down -v

        # Remove images
        docker rmi geneweb-python:latest 2>/dev/null || true

        # Clean Docker system
        docker system prune -f

        log_success "Nettoyage terminé!"
    else
        log_info "Nettoyage annulé."
    fi
}

# Show container status
show_status() {
    log_info "Statut des conteneurs GenEWeb:"
    echo

    if docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "(geneweb|NAMES)"; then
        echo
    else
        log_warning "Aucun conteneur GenEWeb trouvé."
        log_info "Démarrez les services avec: $0 start"
    fi
}

# Main script logic
main() {
    check_dependencies

    case "${1:-help}" in
        "build")
            build_image
            ;;
        "start")
            start_service "" "$2"
            ;;
        "dev")
            start_service "dev" "$2"
            ;;
        "admin")
            start_service "admin" "$2"
            ;;
        "fullstack")
            start_service "fullstack" "$2"
            ;;
        "stop")
            stop_services
            ;;
        "restart")
            restart_services "$2" "$3"
            ;;
        "logs")
            show_logs "$2"
            ;;
        "shell")
            open_shell
            ;;
        "clean")
            clean_resources
            ;;
        "status")
            show_status
            ;;
        "help"|"--help"|"-h")
            show_help
            ;;
        *)
            log_error "Commande inconnue: $1"
            echo
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
