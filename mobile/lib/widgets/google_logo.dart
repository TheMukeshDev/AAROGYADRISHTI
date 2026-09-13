import 'package:flutter/material.dart';

class GoogleLogo extends StatelessWidget {
  const GoogleLogo({super.key, this.size = 22});

  final double size;

  @override
  Widget build(BuildContext context) {
    return Text(
      'G',
      style: TextStyle(
        color: const Color(0xFF4285F4),
        fontSize: size,
        fontWeight: FontWeight.w800,
        height: 1,
      ),
    );
  }
}