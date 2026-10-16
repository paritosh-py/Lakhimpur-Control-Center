import 'package:flutter/material.dart';

class NotificationSection extends StatelessWidget {
  final String title;
  final List<Widget> children;

  const NotificationSection({
    super.key,
    required this.title,
    required this.children,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: const TextStyle(
            fontSize: 15,
            fontWeight: FontWeight.w700,
            color: Colors.black87,
          ),
        ),

        const SizedBox(height: 10),

        Material(
          color: Colors.transparent,
          borderRadius: BorderRadius.circular(20),
          child: Ink(
            width: double.infinity,
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: Colors.grey.shade200),
            ),
            child: Column(children: children),
          ),
        ),
      ],
    );
  }
}
