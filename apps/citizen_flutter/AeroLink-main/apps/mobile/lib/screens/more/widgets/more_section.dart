import 'package:flutter/material.dart';

class MoreSection extends StatelessWidget {
  final String title;
  final List<Widget> children;

  const MoreSection({super.key, required this.title, required this.children});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title.toUpperCase(),
          style: TextStyle(
            fontSize: 11,
            fontWeight: FontWeight.w700,
            letterSpacing: 0.8,
            color: Colors.grey[600],
          ),
        ),

        const SizedBox(height: 8),

        Container(
          width: double.infinity,
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(18),
            border: Border.all(color: Colors.grey.shade200),
          ),
          child: Column(children: _addDividers(children)),
        ),
      ],
    );
  }

  List<Widget> _addDividers(List<Widget> items) {
    final List<Widget> result = [];

    for (int i = 0; i < items.length; i++) {
      result.add(items[i]);

      if (i < items.length - 1) {
        result.add(
          Padding(
            padding: const EdgeInsets.only(left: 16),
            child: Divider(height: 1, color: Colors.grey.shade200),
          ),
        );
      }
    }

    return result;
  }
}
