import { createFileRoute, useNavigate } from '@tanstack/react-router'
import {
  VStack,
  Text,
  Container,
  Input,
  Box
} from '@chakra-ui/react'
import { useForm } from 'react-hook-form'
import { useState } from 'react'
import { FiLock } from 'react-icons/fi'
import { Button } from '../../components/ui/button'
import { Form } from '../../components/ui/form'
import { useServiceMutation, transformApiError } from '../../client/serviceHooks'
import { tokens } from '../../tokens/getTokens'
import { toaster } from '../../components/ui'

interface ForgotPasswordForm {
  usernameEmail: string
}

function ForgotPasswordComponent() {
  const navigate = useNavigate()
  const [isSuccess, setIsSuccess] = useState(false)
  const { color: colors, semantic } = tokens

  const fonts = {
    heading: "GeneralSans, sans-serif",
    body: "GeneralSans, sans-serif",
  }

  const forgotPasswordMutation = useServiceMutation(
    'auth',
    'sendForgotPasswordPasswordForgotPost',
    {
      onSuccess: () => {
        setIsSuccess(true)
      },
      onError: (error) => {
        console.log('Mutation onError callback - Raw error:', error)
        const transformedError = transformApiError(error)

        // Show error toast directly
        toaster.create({
          title: 'Error',
          description: transformedError.message,
          type: 'error',
          duration: 7000,
          meta: {
            closable: true,
          },
        })
      },
    }
  )

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ForgotPasswordForm>()

  const onSubmit = async (data: ForgotPasswordForm) => {
    await forgotPasswordMutation.mutateAsync({
      usernameEmail: data.usernameEmail,
    })
  }

  return (
    <Box bg={colors.background.default} minH="100vh">
      <Container maxW="2xl" py={{ base: 12, md: 20 }}>
        <VStack gap={8}>
          {/* Header */}
          <VStack gap={4} textAlign="center">
            <Box
              p={4}
              borderRadius="full"
              bg={colors.background.elevated}
              color={colors.brand.primary}
              border="2px solid"
              borderColor={colors.brand.primary}
            >
              <FiLock size={32} />
            </Box>

            <Text
              fontSize={{ base: "3xl", md: "4xl" }}
              fontWeight="bold"
              color={colors.foreground.default}
              lineHeight="shorter"
              fontFamily={fonts.heading}
            >
              Forgot Your{" "}
              <Text as="span" color={colors.brand.primary}>
                Password?
              </Text>
            </Text>
            <Text
              color={colors.foreground.muted}
              fontFamily={fonts.body}
              fontSize="lg"
              maxW="md"
            >
              No worries! Enter your email address and we'll send you a link to reset your password.
            </Text>
          </VStack>

          {/* Form */}
          <Form maxW="md" w="full">
            <VStack gap={6}>
              {isSuccess ? (
                <VStack gap={6} textAlign="center" py={8}>
                  <Text
                    fontSize="2xl"
                    fontWeight="semibold"
                    color={colors.brand.primary}
                    fontFamily={fonts.heading}
                  >
                    Check Your Email!
                  </Text>
                  <Text
                    color={colors.foreground.muted}
                    fontFamily={fonts.body}
                    fontSize="lg"
                  >
                    We've sent a password reset link to your email address. Please check your inbox and follow the instructions to reset your password.
                  </Text>
                  <Text
                    color={colors.foreground.muted}
                    fontFamily={fonts.body}
                    fontSize="sm"
                  >
                    We typically respond within 24 hours during business days.
                  </Text>
                  <VStack gap={3} w="full" pt={4}>
                    <Button
                      onClick={() => navigate({ to: '/' })}
                      size="lg"
                      bg={semantic.button.primary.bg.default}
                      color={semantic.button.primary.fg.default}
                      w="full"
                      fontSize="lg"
                      fontFamily={fonts.body}
                    >
                      Back to Home
                    </Button>
                    <Button
                      onClick={() => setIsSuccess(false)}
                      variant="ghost"
                      color={colors.brand.primary}
                      fontFamily={fonts.body}
                    >
                      Try Different Email
                    </Button>
                  </VStack>
                </VStack>
              ) : (
                <VStack gap={6} w="full" as="form" onSubmit={handleSubmit(onSubmit)}>
                  <VStack gap={2} w="full">
                    <Text
                      color={colors.foreground.default}
                      fontFamily={fonts.body}
                      fontWeight="medium"
                      alignSelf="flex-start"
                    >
                      Email or Username *
                    </Text>
                    <Input
                      {...register('usernameEmail', {
                        required: 'Email or username is required',
                        pattern: {
                          value: /^[^\s@]+@[^\s@]+\.[^\s@]+$|^[a-zA-Z0-9_]+$/,
                          message: 'Please enter a valid email or username',
                        },
                      })}
                      placeholder="Enter your email or username"
                      size="lg"
                      bg={colors.background.elevated}
                      border="2px solid"
                      borderColor={colors.border.default}
                      color={colors.foreground.default}
                      _placeholder={{
                        color: colors.foreground.muted,
                      }}
                      _focus={{
                        borderColor: colors.brand.primary,
                        boxShadow: `0 0 0 1px ${colors.brand.primary}`,
                      }}
                      fontFamily={fonts.body}
                    />
                    {errors.usernameEmail && (
                      <Text
                        color="red.500"
                        fontSize="sm"
                        alignSelf="flex-start"
                        fontFamily={fonts.body}
                      >
                        {errors.usernameEmail.message}
                      </Text>
                    )}
                  </VStack>

                  <Button
                    type="submit"
                    loading={isSubmitting && !forgotPasswordMutation.isError}
                    size="lg"
                    bg={semantic.button.primary.bg.default}
                    color={semantic.button.primary.fg.default}
                    w="full"
                    fontSize="lg"
                    fontFamily={fonts.body}
                  >
                    Send Reset Link
                  </Button>

                  <Text
                    fontSize="sm"
                    textAlign="center"
                    color={colors.foreground.muted}
                    fontFamily={fonts.body}
                  >
                    Remember your password?{' '}
                    <Text
                      as="button"
                      onClick={() => navigate({ to: '/' })}
                      color={colors.brand.primary}
                      fontWeight="medium"
                      textDecoration="underline"
                      cursor="pointer"
                    >
                      Back to Home
                    </Text>
                  </Text>
                </VStack>
              )}
            </VStack>
          </Form>
        </VStack>
      </Container>
    </Box>
  )
}

export const Route = createFileRoute('/_layout/forgot-password')({
  component: ForgotPasswordComponent,
})
