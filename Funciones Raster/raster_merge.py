def raster_merge(
    tifs: Iterable[Union[str, Path]],
    d_type: str = "float32",
    compress: Optional[str] = "lzw",
    tiled: bool = True,
    bigtiff: str = "IF_SAFER",
) -> Tuple[np.ndarray, dict]:
    """
    Genera un mosaico a partir de una lista de archivos GeoTIFF (solo float).
    Las áreas sin cobertura y/o NoData se representan como NaN.

    Args:
        tifs:
            Iterable de paths a GeoTIFFs.
        d_type:
            Tipo de dato de salida. Válidos: "float32", "float64".
        compress:
            Compresión GeoTIFF (por ejemplo "lzw", "deflate", o None).
        tiled:
            Si True, escribe el GeoTIFF como tiled (recomendado para 
            rasters grandes).
        bigtiff:
            Política BigTIFF: "IF_SAFER", "YES", "NO".

    Returns:
        mosaic:
            numpy array con shape (bands, rows, cols) y dtype float32/float64.
        profile:
            diccionario con metadatos listo para rasterio.open(..., "w",
            **profile).

    Raises:
        ValueError, FileNotFoundError, rasterio.errors.RasterioIOError,
        RuntimeError
    """
    tifs = list(tifs)
    if not tifs:
        raise ValueError("La lista 'tifs' está vacía. Debe contener al menos un GeoTIFF.")

    # Validar dtype float
    if d_type not in ("float32", "float64"):
        raise ValueError("Esta función es solo para floats. Usá d_type='float32' o 'float64'.")

    np_dtype = np.dtype(d_type)

    # Verificar existencia
    paths: List[Path] = []
    missing: List[str] = []
    for p in tifs:
        pp = Path(p)
        if not pp.exists():
            missing.append(str(pp))
        else:
            paths.append(pp)
    if missing:
        raise FileNotFoundError(
            f"No se encontraron {len(missing)} archivos GeoTIFF:\n- " + "\n- ".join(missing)
        )

    srcs = [] # lista de almacenamiento nombres de raster abiertos
    try:
        # Abrir rasters
        for p in paths:
            try:
                srcs.append(rasterio.open(p))
            except Exception as e:
                raise rasterio.errors.RasterioIOError(f"No se pudo abrir el GeoTIFF: {p}") from e

        # Validaciones básicas de compatibilidad
        crs0 = srcs[0].crs # Verifico que todos tengan el mismo crs
        count0 = srcs[0].count # Verifico la cantida de bandas
        for s in srcs[1:]:
            if s.crs != crs0:
                raise ValueError("Los GeoTIFFs tienen CRS distintos. Reproyectá antes de mosaicar.")
            if s.count != count0:
                raise ValueError("Los GeoTIFFs tienen distinta cantidad de bandas. Unificá antes de mosaicar.")

        # Merge: Valores hueco como 'NAN'
        try:
            mosaic, out_transform = merge(srcs, nodata=np.nan)
        except Exception as e:
            raise RuntimeError("Falló rasterio.merge.merge() al generar el mosaico.") from e

        # Forzar dtype float
        mosaic = mosaic.astype(np_dtype, copy=False)

        # Profile de salida
        profile = srcs[0].profile.copy()
        profile.update(
            driver="GTiff",
            height=mosaic.shape[1],
            width=mosaic.shape[2],
            transform=out_transform,
            count=mosaic.shape[0],
            dtype=str(np_dtype),
            nodata=np.nan,
            compress=compress,
            tiled=bool(tiled),
            BIGTIFF=bigtiff,
        )

        return mosaic, profile

    finally:
        for s in srcs:
            try:
                s.close()
            except Exception:
                pass