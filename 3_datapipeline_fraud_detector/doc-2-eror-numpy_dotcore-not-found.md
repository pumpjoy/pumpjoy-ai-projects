# Troubleshooting Summary: PySpark Dependency Issue

## So far:
Successfully execute a PySpark Structured Streaming application that uses external Python dependencies (`pandas`, `numpy`, `scikit-learn` for Isolation Forest inference) inside a Docker container built from the base image `apache/spark:3.5.7-scala2.12-java11-python3-ubuntu`.

## Issue: `ModuleNotFoundError`
The application consistently failed at the import stage with either `ModuleNotFoundError: No module named 'numpy._core'`.

This occurred despite confirming that the packages were successfully installed inside the container via `docker exec spark-master pip list`.

## Root Cause Analysis
The failure was not due to missing files but a **corrupted Python execution path** caused by a conflict between three different environments:

1.  **Package Installation Path:** Where `pip` physically placed the files.
2.  **System PATH:** The OS environment variables that couldn't find the `python` executable by name.
3.  **PySpark Driver/Executor Path:** The specific, restricted Python path configured by the Spark JVM process.
4.  **Binary Mismatch:** The core binary files of NumPy (`numpy._core`) were compiled against system libraries that differed from those used when the PySpark JVM launched the Python subprocess, leading to load failure.

---

## Attempted Solutions (Chronological Order)
Attempted to fix the installation, then the pathing, and finally, the environment conflicts. All attempts failed:

| # | Solution Category | Action Taken | Why it Failed |
| :--- | :--- | :--- | :--- |
| **1.** | **Installation** | Added `numpy`, `pandas`, `scikit-learn` to `requirements.txt` and ran `pip install` in the `Dockerfile`. | Initial `pip list` often failed or showed no packages. The packages were not installed in the system's default path. |
| **2.** | **Path Injection (Simple)** | Added `PYTHONPATH: /opt/app_libs` to `docker-compose.yaml` and installed packages there. | PySpark's JVM ignores or overwrites the standard shell `PYTHONPATH` for the Driver process. |
| **3.** | **Binary/Compiling Fix** | Added `build-essential` and `python3-dev` to the `Dockerfile` to ensure a clean binary build. | Did not resolve the `numpy._core` error, confirming the issue was a runtime library mismatch, not a missing compilation tool. |
| **4.** | **Advanced Packaging** | Used the `--archives` flag with a zipped virtual environment (`venv.tar.gz`). | The PySpark Driver/Executor failed to correctly extract and configure the complex Python environment path within the constrained image, reverting to the `ModuleNotFoundError`. |
| **5.** | **Java Dependency Fix** | Added `--conf "spark.driver.extraJavaOptions=-Divy.cache.dir=/tmp"` to fix Ivy cache permissions. | Successful (fixed Java errors) but did not solve the underlying Python path problem. |
| **6.** | **Absolute Path Override** | Confirmed packages were installed and forced the Python interpreter path using **`PYSPARK_PYTHON`** and **`PYSPARK_DRIVER_PYTHON`** in `docker-compose.yaml` and `spark-submit --conf`. | Confirmed that even with the *correct* executable path, the binaries were incompatible with the PySpark subprocess environment, leading to the final, fatal `numpy._core` error. |

## Conclusion

The failure of the absolute path override confirms that the `apache/spark:3.5.7-scala2.12-java11-python3-ubuntu` base image is **structurally incompatible** with external, compiled Python libraries required for Scikit-learn inference.

The only way thus far to achieve the goal of using Pandas UDFs is to solution of **switching the base image to a stable, data-science-focused image** (`jupyter/pyspark-notebook`).


## Basically
- The current program leads to `No module found named 'numpy._core'`.
- Will switch to image `jupyter/pyspark-notebook` to continue development of the full pipeline.