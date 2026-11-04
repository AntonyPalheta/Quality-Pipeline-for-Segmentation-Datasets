def test_quality_pipeline_package_is_importable():
    import quality_pipeline

    assert quality_pipeline.__name__ == "quality_pipeline"