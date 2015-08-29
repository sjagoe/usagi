from mock import Mock


def MockTestCase():
    case = Mock()
    case.assertEqual = Mock()
    case.assertIn = Mock()
    case.assertIn = Mock()
    case.assertRegexpMatches = Mock()
    return case
