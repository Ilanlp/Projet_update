import mlflow
import mlflow.sklearn
from sklearn.model_selection import GridSearchCV
import numpy as np

class MLflowGridSearchCV(GridSearchCV):
    """Extension de GridSearchCV avec intégration MLflow."""
    
    def __init__(self, estimator, param_grid, scoring=None, n_jobs=None,
                 cv=None, verbose=0, pre_dispatch='2*n_jobs',
                 error_score=np.nan, return_train_score=False):
        """Initialise MLflowGridSearchCV avec les mêmes paramètres que GridSearchCV."""
        super().__init__(
            estimator=estimator,
            param_grid=param_grid,
            scoring=scoring,
            n_jobs=n_jobs,
            cv=cv,
            verbose=verbose,
            pre_dispatch=pre_dispatch,
            error_score=error_score,
            return_train_score=return_train_score
        )
    
    def fit(self, X, y=None, groups=None, **fit_params):
        """Exécute la recherche sur grille et log les résultats dans MLflow."""
        with mlflow.start_run() as run:
            # Log des paramètres de base
            params = {
                "cv_folds": str(self.cv),
                "scoring": str(self.scoring),
                "n_jobs": str(self.n_jobs)
            }
            mlflow.log_params(params)
            
            # Exécution de GridSearchCV
            super().fit(X, y, groups=groups, **fit_params)
            
            # Log des meilleurs paramètres
            mlflow.log_params({
                k: str(v) for k, v in self.best_params_.items()
            })
            
            # Log des métriques
            metrics = {
                "best_score": float(self.best_score_),
                "mean_cv_score": float(self.cv_results_['mean_test_score'].mean()),
                "std_cv_score": float(self.cv_results_['std_test_score'].mean())
            }
            mlflow.log_metrics(metrics)
            
            # Log du meilleur modèle
            mlflow.sklearn.log_model(
                sk_model=self.best_estimator_,
                artifact_path="best_model",
                registered_model_name="job_matching_model"
            )
            
        return self 