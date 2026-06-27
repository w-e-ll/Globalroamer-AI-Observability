#!/usr/bin/env python3
# -*- coding: utf-8 -*-


class GlobalRoamerAIException(Exception):
    """
    Base application exception.
    """
    pass


class ConfigError(GlobalRoamerAIException):
    """
    Configuration loading/parsing failure.
    """
    pass


class TraceLoaderError(GlobalRoamerAIException):
    """
    Trace file loading failure.
    """
    pass


class TraceParserError(GlobalRoamerAIException):
    """
    Trace parsing failure.
    """
    pass


class TraceNormalizationError(GlobalRoamerAIException):
    """
    Trace normalization failure.
    """
    pass


class TraceChunkingError(GlobalRoamerAIException):
    """
    Chunk creation failure.
    """
    pass


class EmbeddingGenerationError(GlobalRoamerAIException):
    """
    Embedding generation failure.
    """
    pass


class VectorStoreError(GlobalRoamerAIException):
    """
    Vector DB operation failure.
    """
    pass


class SimilaritySearchError(GlobalRoamerAIException):
    """
    Similarity retrieval failure.
    """
    pass


class AISummaryError(GlobalRoamerAIException):
    """
    AI summary generation failure.
    """
    pass


class RootCauseAnalysisError(GlobalRoamerAIException):
    """
    AI root cause analysis failure.
    """
    pass


class RetryAdvisorError(GlobalRoamerAIException):
    """
    Retry intelligence evaluation failure.
    """
    pass


class CampaignHealthError(GlobalRoamerAIException):
    """
    Campaign health scoring failure.
    """
    pass


class ReportGenerationError(GlobalRoamerAIException):
    """
    Final report generation failure.
    """
    pass
