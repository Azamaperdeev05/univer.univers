from functions.get_attestation import Attestation
from functions.get_attendance import Attendance
from type import Mark, ActiveMark


def _get_attestation_by_subject(
    attestations: list[Attestation], subject: str
) -> Attestation:
    for attestation in attestations:
        if attestation.subject == subject:
            return attestation
    return None


def _join_marks(a: list[Mark], b: list[Mark]) -> list[Mark]:
    result: list[Mark] = []
    is_active_set = False
    for index, a_mark in enumerate(a):
        if index >= len(b):
            result.append(a_mark)
            break
        b_mark = b[index]
        result_mark = b_mark or a_mark
        if not is_active_set and a_mark.value == 0:
            result_mark = ActiveMark(title=result_mark.title, value=result_mark.value)
            is_active_set = True
        result.append(result_mark)
    return result


def merge_attestation_attendance(
    attestations: list[Attestation], attendances: list[Attendance]
):
    no_attestation = len(attestations) < 1
    for attendance in attendances:
        attestation = _get_attestation_by_subject(attestations, attendance.subject)
        if no_attestation:
            new_attestation = [Mark(title, 0) for title, _ in attendance.summary]
            attestation = Attestation(
                subject=attendance.subject,
                attestation=new_attestation + [Mark(title="", value=0)],
                attendance=[],
            )
            attestations.append(attestation)
        if attestation is None:
            continue
        attestation.attestation = _join_marks(
            attestation.attestation, attendance.summary
        )
        attestation.attendance = attendance.attendance
    return sorted(attestations, key=lambda a: a.subject)
