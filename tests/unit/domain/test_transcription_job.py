import pytest
from uuid import uuid4

from app.domain.entities.transcription_job import TranscriptionJob, MAX_RETRIES
from app.domain.value_objects.job_status import JobStatus
from app.domain.exceptions import InvalidStateTransitionError, MaxRetriesExceededError


@pytest.fixture
def audio_file_id():
    return uuid4()


class TestTranscriptionJobCreation:
    """Tests for initial TranscriptionJob state."""

    def test_new_job_starts_in_pending_status_with_zero_progress(self, audio_file_id):
        job = TranscriptionJob(audio_file_id=audio_file_id)
        assert job.status == JobStatus.PENDING
        assert job.progress_percent == 0


class TestTranscriptionJobTransitions:
    """Tests for valid and invalid state transitions."""

    def test_pending_to_converting(self, audio_file_id):
        job = TranscriptionJob(audio_file_id=audio_file_id)
        job.transition_to(JobStatus.CONVERTING)
        assert job.status == JobStatus.CONVERTING

    def test_converting_to_transcribing(self, audio_file_id):
        job = TranscriptionJob(audio_file_id=audio_file_id)
        job.transition_to(JobStatus.CONVERTING)
        job.transition_to(JobStatus.TRANSCRIBING)
        assert job.status == JobStatus.TRANSCRIBING

    def test_transcribing_to_completed(self, audio_file_id):
        job = TranscriptionJob(audio_file_id=audio_file_id)
        job.transition_to(JobStatus.CONVERTING)
        job.transition_to(JobStatus.TRANSCRIBING)
        job.transition_to(JobStatus.COMPLETED)
        assert job.status == JobStatus.COMPLETED

    def test_any_state_to_failed(self, audio_file_id):
        job_pending = TranscriptionJob(audio_file_id=audio_file_id)
        job_pending.transition_to(JobStatus.FAILED)
        assert job_pending.status == JobStatus.FAILED

        job_converting = TranscriptionJob(audio_file_id=audio_file_id)
        job_converting.transition_to(JobStatus.CONVERTING)
        job_converting.transition_to(JobStatus.FAILED)
        assert job_converting.status == JobStatus.FAILED

        job_transcribing = TranscriptionJob(audio_file_id=audio_file_id)
        job_transcribing.transition_to(JobStatus.CONVERTING)
        job_transcribing.transition_to(JobStatus.TRANSCRIBING)
        job_transcribing.transition_to(JobStatus.FAILED)
        assert job_transcribing.status == JobStatus.FAILED

    def test_invalid_transition_raises_error(self, audio_file_id):
        job = TranscriptionJob(audio_file_id=audio_file_id)
        with pytest.raises(InvalidStateTransitionError):
            job.transition_to(JobStatus.COMPLETED)

    def test_completed_to_any_raises_error(self, audio_file_id):
        job = TranscriptionJob(audio_file_id=audio_file_id)
        job.transition_to(JobStatus.CONVERTING)
        job.transition_to(JobStatus.TRANSCRIBING)
        job.transition_to(JobStatus.COMPLETED)

        with pytest.raises(InvalidStateTransitionError):
            job.transition_to(JobStatus.PENDING)

        with pytest.raises(InvalidStateTransitionError):
            job.transition_to(JobStatus.CONVERTING)

        with pytest.raises(InvalidStateTransitionError):
            job.transition_to(JobStatus.TRANSCRIBING)

        with pytest.raises(InvalidStateTransitionError):
            job.transition_to(JobStatus.FAILED)


class TestTranscriptionJobProgress:
    """Tests for progress updates."""

    def test_update_progress_clamps_to_0_100(self, audio_file_id):
        job = TranscriptionJob(audio_file_id=audio_file_id)

        job.update_progress(50)
        assert job.progress_percent == 50

        job.update_progress(-10)
        assert job.progress_percent == 0

        job.update_progress(150)
        assert job.progress_percent == 100


class TestTranscriptionJobFailure:
    """Tests for job failure handling."""

    def test_fail_sets_error_message_and_transitions_to_failed(self, audio_file_id):
        job = TranscriptionJob(audio_file_id=audio_file_id)
        job.fail("Something went wrong")
        assert job.status == JobStatus.FAILED
        assert job.error_message == "Something went wrong"


class TestTranscriptionJobRetry:
    """Tests for job retry behavior."""

    def test_retry_transitions_failed_to_pending(self, audio_file_id):
        job = TranscriptionJob(audio_file_id=audio_file_id)
        job.fail("Temporary error")
        job.retry()
        assert job.status == JobStatus.PENDING
        assert job.retry_count == 1
        assert job.error_message is None
        assert job.progress_percent == 0

    def test_retry_raises_max_retries_exceeded_error(self, audio_file_id):
        job = TranscriptionJob(audio_file_id=audio_file_id)
        for i in range(MAX_RETRIES):
            job.fail(f"Error attempt {i}")
            job.retry()

        job.fail("Final error")
        with pytest.raises(MaxRetriesExceededError, match="exceeded maximum retries"):
            job.retry()


class TestTranscriptionJobIsTerminal:
    """Tests for is_terminal property."""

    def test_is_terminal_true_for_completed(self, audio_file_id):
        job = TranscriptionJob(audio_file_id=audio_file_id)
        job.transition_to(JobStatus.CONVERTING)
        job.transition_to(JobStatus.TRANSCRIBING)
        job.transition_to(JobStatus.COMPLETED)
        assert job.is_terminal is True

    def test_is_terminal_true_for_failed_with_max_retries(self, audio_file_id):
        job = TranscriptionJob(audio_file_id=audio_file_id)
        for i in range(MAX_RETRIES):
            job.fail(f"Error {i}")
            job.retry()

        job.fail("Final failure")
        assert job.retry_count == MAX_RETRIES
        assert job.is_terminal is True

    def test_is_terminal_false_for_failed_with_retries_remaining(self, audio_file_id):
        job = TranscriptionJob(audio_file_id=audio_file_id)
        job.fail("Recoverable error")
        assert job.retry_count < MAX_RETRIES
        assert job.is_terminal is False
