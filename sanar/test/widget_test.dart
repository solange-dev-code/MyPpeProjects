import 'package:flutter_test/flutter_test.dart';
import 'package:sanar/main.dart';

void main() {
  testWidgets('Sanar smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(const SanarApp());
  });
}