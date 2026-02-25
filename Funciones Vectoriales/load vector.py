#=========================================================
# FUNCIONES VECTORES
#========================================================

def load_vector(vector_path: Union[str, Path], target_crs) -> gpd.GeoDataFrame:
    """
    Carga un vector y verifica que su CRS sea el especificado.
    Si el CRS es diferente al especificado, reproyecta automáticamente el vector.

    Args:
        vector_path: Ruta al archivo vectorial.
        target_crs: CRS destino (por ejemplo, CRS de los tiles DEM).

    Returns:
        GeoDataFrame en el CRS objetivo.

    Raises:
        FileNotFoundError: Si no existe el archivo.
        ValueError: Si el vector no tiene CRS definido o target_crs es inválido.
        RuntimeError: Si ocurre un error inesperado al leer/procesar el vector.
    """
    vector_path = Path(vector_path)
    try:
        # 1) Verificar existencia de archivo
        if not vector_path.exists():
            raise FileNotFoundError(f"No existe la ruta especificada: {vector_path}")

        # 2) Cargar vector
        gdf = gpd.read_file(vector_path)

        # 3) Verificar CRS del vector
        if gdf.crs is None:
            raise ValueError("El vector no tiene CRS definido.")

        # 4) Validar CRS de destino
        try:
            dst_crs = CRS.from_user_input(target_crs)
        except Exception as e:
            raise ValueError(f"target_crs inválido: {target_crs}") from e

        src_crs = CRS.from_user_input(gdf.crs)

        # 5) Reproyectar solo si es necesario
        if src_crs != dst_crs:
            gdf = gdf.to_crs(dst_crs)

        return gdf

    except (FileNotFoundError, ValueError):
        # Re-lanza errores esperados con su mensaje original
        raise

    except Exception as e:
        # Captura cualquier otro error no previsto
        raise RuntimeError(f"Error al cargar/reproyectar el vector: {e}") from e
