"""Module pour nettoyer les ressources système."""

import os
import signal
import multiprocessing as mp
from typing import List

def get_semaphores() -> List[str]:
    """Récupère la liste des sémaphores du système."""
    try:
        # Sur Linux, les sémaphores sont dans /dev/shm/
        sem_path = "/dev/shm"
        if os.path.exists(sem_path):
            return [f for f in os.listdir(sem_path) if f.startswith("sem.")]
    except Exception:
        pass
    return []

def clean_up() -> None:
    """Nettoie les ressources système (sémaphores, processus)."""
    # Nettoyer les sémaphores
    for sem in get_semaphores():
        try:
            os.unlink(os.path.join("/dev/shm", sem))
        except Exception:
            pass

    # Nettoyer les processus
    for p in mp.active_children():
        try:
            if p.pid is not None:  # Vérifier que le PID existe
                os.kill(p.pid, signal.SIGTERM)
        except Exception:
            pass 