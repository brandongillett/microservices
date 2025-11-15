import { Text } from "@chakra-ui/react";
import { useState, useEffect } from "react";
import { tokens } from "@/tokens/getTokens";

interface TypewriterTextProps {
	text: string;
	brandStartIndex: number; // Index where brand color starts
	fontSize: object;
	fontWeight: string;
	lineHeight: string;
	fontFamily: string;
}

export function TypewriterText({
	text,
	brandStartIndex,
	fontSize,
	fontWeight,
	lineHeight,
	fontFamily,
}: TypewriterTextProps) {
	const [currentIndex, setCurrentIndex] = useState(0);
	const [showCursor, setShowCursor] = useState(true);
	const [isTyping, setIsTyping] = useState(true);
	const [isComplete, setIsComplete] = useState(false);

	const { color: colors } = tokens;

	useEffect(() => {
		if (currentIndex < text.length) {
			const speed = Math.random() * 100 + 80;
			const timer = setTimeout(() => {
				setCurrentIndex(currentIndex + 1);
			}, speed);

			return () => clearTimeout(timer);
		} else {
			setIsTyping(false);
			setIsComplete(true);
			setShowCursor(false);
		}
	}, [currentIndex, text.length]);

	useEffect(() => {
		if (!isComplete) {
			if (isTyping) {
				// Keep cursor solid while typing
				setShowCursor(true);
			} else {
				// Blink cursor after typing is done
				const cursorTimer = setInterval(() => {
					setShowCursor(prev => !prev);
				}, 530);

				return () => clearInterval(cursorTimer);
			}
		}
	}, [isTyping, isComplete]);

	const renderText = () => {
		const visibleText = text.slice(0, currentIndex);
		const beforeBrand = visibleText.slice(0, brandStartIndex);
		const brandPart = visibleText.slice(brandStartIndex);

		return (
			<>
				<Text as="span" color={colors.foreground.default}>
					{beforeBrand}
				</Text>
				<Text as="span" color={colors.brand.primary}>
					{brandPart}
				</Text>
				{!isComplete && showCursor && (
					<Text
						as="span"
						color={currentIndex >= brandStartIndex ? colors.brand.primary : colors.foreground.default}
						opacity={1}
					>
						|
					</Text>
				)}
			</>
		);
	};

	return (
		<Text
			fontSize={fontSize}
			fontWeight={fontWeight}
			lineHeight={lineHeight}
			fontFamily={fontFamily}
		>
			{renderText()}
		</Text>
	);
}
