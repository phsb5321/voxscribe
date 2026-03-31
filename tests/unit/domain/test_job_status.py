from app.domain.value_objects.job_status import JobStatus


class TestDownloadingStateTransitions:
    """Tests for the DOWNLOADING state in the job status state machine."""

    def test_pending_to_downloading_is_valid(self):
        assert JobStatus.PENDING.can_transition_to(JobStatus.DOWNLOADING) is True

    def test_downloading_to_converting_is_valid(self):
        assert JobStatus.DOWNLOADING.can_transition_to(JobStatus.CONVERTING) is True

    def test_downloading_to_failed_is_valid(self):
        assert JobStatus.DOWNLOADING.can_transition_to(JobStatus.FAILED) is True

    def test_converting_to_downloading_is_invalid(self):
        assert JobStatus.CONVERTING.can_transition_to(JobStatus.DOWNLOADING) is False

    def test_downloading_to_completed_is_invalid(self):
        assert JobStatus.DOWNLOADING.can_transition_to(JobStatus.COMPLETED) is False

    def test_downloading_to_transcribing_is_invalid(self):
        assert JobStatus.DOWNLOADING.can_transition_to(JobStatus.TRANSCRIBING) is False

    def test_pending_to_converting_still_valid(self):
        """File uploads skip DOWNLOADING and go directly to CONVERTING."""
        assert JobStatus.PENDING.can_transition_to(JobStatus.CONVERTING) is True
