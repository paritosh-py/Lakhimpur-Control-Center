import 'package:flutter/material.dart';

class EmergencyServiceRow extends StatelessWidget {
  final String title;
  final String subtitle;
  final String number;
  final IconData icon;

  const EmergencyServiceRow({
    super.key,
    required this.title,
    required this.subtitle,
    required this.number,
    required this.icon,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 10),
      child: Row(
        children: [
          Icon(icon, size: 21, color: const Color(0xFFE53935)),

          const SizedBox(width: 13),

          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: const TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w700,
                  ),
                ),

                const SizedBox(height: 2),

                Text(
                  subtitle,
                  style: TextStyle(fontSize: 11, color: Colors.grey),
                ),
              ],
            ),
          ),

          Text(
            number,
            style: const TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.w700,
              color: Color(0xFFE53935),
            ),
          ),
        ],
      ),
    );
  }
}
