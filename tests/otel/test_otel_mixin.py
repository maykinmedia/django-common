from unittest import TestCase

from opentelemetry.metrics import Observation

from maykin_common.tests.otel import MetricsAssertMixin


class MetricsAssertMixinTests(MetricsAssertMixin, TestCase):
    def test_assert_marked_global_success(self):
        result = [
            Observation(value=1, attributes={"scope": "global"}),
            Observation(value=2, attributes={"scope": "global"}),
        ]
        self.assertMarkedGlobal(result)

    def test_assert_marked_global_failure(self):
        result = [
            Observation(value=1, attributes={"scope": "global"}),
            Observation(value=2, attributes={"scope": "local"}),
        ]
        with self.assertRaises(AssertionError):
            self.assertMarkedGlobal(result)

    def test_group_observations_by_groups_and_sums(self):
        result = [
            Observation(value=1, attributes={"form": "A"}),
            Observation(value=2, attributes={"form": "A"}),
            Observation(value=3, attributes={"form": "B"}),
        ]
        grouped = self._group_observations_by(result, "form")
        self.assertEqual(grouped, {"A": 3, "B": 3})

    def test_group_observations_by_assertions(self):
        # attributes == None
        result = [Observation(value=1, attributes=None)]
        with self.assertRaises(AssertionError):
            self._group_observations_by(result, "form")

        # type(attributes) != str
        result = [Observation(value=1, attributes={"form": 123})]
        with self.assertRaises(AssertionError):
            self._group_observations_by(result, "form")
